from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.song import SongResponse, SongCreate
from app.services.playlist_service import LikeService
from app.utils.security import decode_token
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from typing import List

router = APIRouter(prefix="/likes", tags=["likes"])
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return payload

@router.post("/{song_id}", response_model=SongResponse)
def like_song(song_id: int, db: Session = Depends(get_db), payload = Depends(verify_token)):
    """Like a song by its ID (song must already exist in database)"""
    user_id = int(payload.get("sub"))
    return LikeService.like_song(db, song_id, user_id)

@router.post("/with-data", response_model=SongResponse)
def like_song_with_data(
    song_data: SongCreate,
    db: Session = Depends(get_db),
    payload = Depends(verify_token)
):
    """
    Like a song by providing full song data.
    If the song doesn't exist in the database, it will be created automatically.
    Returns the full song data including: id, title, artist, album, genre, duration, url, image_url, etc.
    
    Example request body:
    {
        "title": "Popular",
        "artist": "Ariana Grande",
        "album": "Wicked",
        "genre": "Pop",
        "duration": 30.0,
        "url": "https://...",
        "image_url": "https://..."
    }
    """
    user_id = int(payload.get("sub"))
    return LikeService.like_song_with_data(db, song_data, user_id)

@router.delete("/{song_id}")
def unlike_song(song_id: int, db: Session = Depends(get_db), payload = Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return LikeService.unlike_song(db, song_id, user_id)

@router.get("", response_model=List[SongResponse])
def get_user_likes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    payload = Depends(verify_token)
):
    user_id = int(payload.get("sub"))
    return LikeService.get_user_likes(db, user_id, skip, limit)
