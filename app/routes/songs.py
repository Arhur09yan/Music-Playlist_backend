from typing import List
from pathlib import Path
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.song import SongCreate, SongResponse, SongUpdate
from app.services.song_service import SongService
from app.services.spotify_service import SpotifyService
from app.services.audio_service import AudioService
from app.utils.security import decode_token
from app.models.song import Song

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/songs", tags=["songs"])
security = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return payload

def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[int]:
    """Get user_id from token if available, otherwise return None."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload:
            return int(payload.get("sub"))
    except:
        pass
    return None


@router.post("", response_model=SongResponse)
def create_song(song: SongCreate, db: Session = Depends(get_db), payload=Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return SongService.create_song(db, song, user_id)


@router.get("", response_model=List[SongResponse])
def get_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_optional_user_id),
):
    """Get all songs with liked status. Authentication is optional - if provided, liked status will be accurate."""
    return SongService.get_all_songs(db, skip, limit, user_id)


@router.get("/{song_id}", response_model=SongResponse)
def get_song(
    song_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_optional_user_id),
):
    """Get a song by ID with liked status. Authentication is optional - if provided, liked status will be accurate."""
    return SongService.get_song(db, song_id, user_id)


@router.put("/{song_id}", response_model=SongResponse)
def update_song(
    song_id: int,
    song_update: SongUpdate,
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    user_id = int(payload.get("sub"))
    return SongService.update_song(db, song_id, song_update, user_id)


@router.delete("/{song_id}")
def delete_song(song_id: int, db: Session = Depends(get_db), payload=Depends(verify_token)):
    return SongService.delete_song(db, song_id)


@router.get("/search/query")
def search_songs(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_optional_user_id),
):
    """Search songs with liked status. Authentication is optional - if provided, liked status will be accurate."""
    songs = SongService.search_songs(db, q, skip, limit, user_id)
    return {"query": q, "results": songs, "count": len(songs)}


@router.post("/import/spotify", response_model=SongResponse)
def import_song_from_spotify(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    """
    Search Spotify for a track using `query`, store the first result as a Song,
    and return the created Song with liked status.
    """
    user_id = int(payload.get("sub"))
    created_song = SpotifyService.import_song_from_spotify(db, query, user_id)
    if not created_song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching track found on Spotify",
        )
    return created_song


@router.post("/import/spotify/bulk", response_model=List[SongResponse])
def import_songs_from_spotify(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    """
    Search Spotify for multiple tracks using `query`, store them as Songs,
    and return the list of created Songs.
    Skips duplicates (songs with same title and artist).
    
    Example queries:
    - "rock music"
    - "jazz classics"
    - "pop hits 2024"
    - "artist: The Beatles"
    """
    try:
        user_id = int(payload.get("sub"))
        created_songs = SpotifyService.import_songs_from_spotify(db, query, limit, user_id)
        if not created_songs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No matching tracks found on Spotify for query: '{query}'. Try a different search term.",
            )
        return created_songs
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing from Spotify: {str(e)}",
        )


@router.get("/test/spotify")
def test_spotify_connection(payload=Depends(verify_token)):
    """
    Test Spotify API connection and credentials.
    Returns connection status and sample search result.
    """
    try:
        from app.config import get_settings
        
        settings = get_settings()
        
        # Check if credentials are set
        if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
            return {
                "status": "error",
                "message": "Spotify credentials not configured",
                "client_id_set": bool(settings.SPOTIFY_CLIENT_ID),
                "client_secret_set": bool(settings.SPOTIFY_CLIENT_SECRET),
            }
        
        # Try to get access token
        try:
            token = SpotifyService._get_access_token()
            token_status = "success" if token else "failed"
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get access token: {str(e)}",
                "credentials_configured": True,
                "error_type": type(e).__name__,
            }
        
        # Try a test search
        try:
            test_track = SpotifyService._search_track_raw("test", limit=1)
            search_status = "success" if test_track else "no_results"
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to search Spotify: {str(e)}",
                "token_obtained": True,
                "error_type": type(e).__name__,
            }
        
        return {
            "status": "success",
            "message": "Spotify API connection working",
            "credentials_configured": True,
            "token_obtained": True,
            "search_working": True,
            "sample_track": {
                "name": test_track.get("name", "N/A"),
                "artist": test_track.get("artists", [{}])[0].get("name", "N/A") if test_track.get("artists") else "N/A",
            } if test_track else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__,
        }


@router.get("/{song_id}/stream")
def stream_song_audio(song_id: int, db: Session = Depends(get_db)):
    """
    Stream audio file for a song.
    Returns the local cached file if available, otherwise streams from original URL.
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found",
        )
    
    # Try to use local file first
    if song.local_file_path:
        file_path = Path(song.local_file_path)
        # If path is relative, make it absolute from backend directory
        if not file_path.is_absolute():
            backend_dir = Path(__file__).parent.parent.parent
            file_path = backend_dir / file_path
        
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                media_type="audio/mpeg",
                filename=f"{song.title.replace(' ', '_')}.mp3"
            )
    
    # Fallback: stream from original URL (if it's a direct audio URL)
    if song.url:
        # Check if it's a playable preview URL
        is_preview_url = (
            "preview" in song.url or 
            "p.scdn.co" in song.url or 
            song.url.endswith(".mp3") or
            song.url.startswith("https://") and ("audio" in song.url.lower() or ".mp3" in song.url.lower())
        )
        
        if is_preview_url:
            import requests
            try:
                response = requests.get(song.url, stream=True, timeout=30)
                response.raise_for_status()
                
                def generate():
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                
                return StreamingResponse(
                    generate(),
                    media_type="audio/mpeg",
                    headers={
                        "Content-Disposition": f'inline; filename="{song.title.replace(" ", "_")}.mp3"'
                    }
                )
            except Exception as e:
                logger.error(f"Error streaming from URL {song.url}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error streaming audio: {str(e)}"
                )
        else:
            # It's a Spotify web URL, not a preview - can't stream it
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This song doesn't have a playable preview. Please import songs with preview URLs."
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Audio file not available"
    )

