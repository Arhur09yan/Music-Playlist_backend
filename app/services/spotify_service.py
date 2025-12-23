from typing import Dict, Any, Optional, List
import json
import logging
import requests

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.song import Song
from app.schemas.song import SongCreate, SongResponse
from app.services.song_service import SongService
from app.services.audio_service import AudioService

logger = logging.getLogger(__name__)
settings = get_settings()


class SpotifyService:
    """
    Spotify import service
    ✔ Fetches metadata from Spotify API
    ✔ Downloads ONLY 30-second preview audio (preview_url)
    ✔ Stores preview locally
    ✔ Saves metadata + local_file_path in DB
    ✔ Spotify ToS compliant
    """

    # ---------------------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------------------
    @staticmethod
    def _get_access_token() -> str:
        if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
            raise ValueError("Spotify credentials not configured")

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    # ---------------------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------------------
    @staticmethod
    def _search_tracks(query: str, limit: int = 20) -> List[Dict[str, Any]]:
        token = SpotifyService._get_access_token()

        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "track", "limit": min(limit, 50)},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return data.get("tracks", {}).get("items", [])

    # ---------------------------------------------------------------------
    # SINGLE SONG IMPORT
    # ---------------------------------------------------------------------
    @staticmethod
    def import_song_from_spotify(
        db: Session,
        query: str,
        user_id: Optional[int] = None,
    ) -> Optional[SongResponse]:

        tracks = SpotifyService._search_tracks(query, limit=1)
        if not tracks:
            return None

        track = tracks[0]

        title = track.get("name", "Unknown Title")
        artist = track.get("artists", [{}])[0].get("name", "Unknown Artist")
        album = track.get("album", {}).get("name", "Unknown Album")
        spotify_url = track.get("external_urls", {}).get("spotify", "")
        preview_url = track.get("preview_url")
        
        # Log preview_url status
        logger.info(f"Track: '{title}' by '{artist}'")
        logger.info(f"  preview_url: {preview_url if preview_url else 'None (no preview available)'}")
        if preview_url:
            logger.info(f"  preview_url value: {preview_url}")
        
        duration = 30.0 if preview_url else track.get("duration_ms", 0) / 1000

        album_images = track.get("album", {}).get("images", [])
        image_url = album_images[0]["url"] if album_images else ""

        # -----------------------------------------------------------------
        # DOWNLOAD PREVIEW (30s ONLY)
        # -----------------------------------------------------------------
        local_file_path = None
        if preview_url:
            try:
                local_file_path = AudioService.download_preview(preview_url)
                logger.info(f"Preview downloaded: {local_file_path}")
            except Exception as e:
                logger.error(f"Preview download failed: {e}")

        # -----------------------------------------------------------------
        # SAVE TO DB
        # -----------------------------------------------------------------
        song_create = SongCreate(
            title=title,
            artist=artist,
            album=album,
            genre="Unknown",
            duration=duration,
            url=spotify_url,                # Spotify external link
            local_file_path=local_file_path,  # 30s preview path
            image_url=image_url,
        )

        return SongService.create_song(db, song_create, user_id)

    # ---------------------------------------------------------------------
    # BULK IMPORT
    # ---------------------------------------------------------------------
    @staticmethod
    def import_songs_from_spotify(
        db: Session,
        query: str,
        limit: int = 20,
        user_id: Optional[int] = None,
    ) -> List[SongResponse]:

        tracks = SpotifyService._search_tracks(query, limit)
        created_songs: List[SongResponse] = []

        for track in tracks:
            title = track.get("name", "Unknown Title")
            artist = track.get("artists", [{}])[0].get("name", "Unknown Artist")

            # Skip duplicates
            if db.query(Song).filter(Song.title == title, Song.artist == artist).first():
                continue

            album = track.get("album", {}).get("name", "Unknown Album")
            spotify_url = track.get("external_urls", {}).get("spotify", "")
            preview_url = track.get("preview_url")
            
            # Log preview_url status
            logger.info(f"Track: '{title}' by '{artist}'")
            logger.info(f"  preview_url: {preview_url if preview_url else 'None (no preview available)'}")
            if preview_url:
                logger.info(f"  preview_url value: {preview_url}")
            
            duration = 30.0 if preview_url else track.get("duration_ms", 0) / 1000

            album_images = track.get("album", {}).get("images", [])
            image_url = album_images[0]["url"] if album_images else ""
            
            # Download preview
            local_file_path = None
            if preview_url:
                try:
                    local_file_path = AudioService.download_preview(preview_url)
                except Exception as e:
                    logger.error(f"Preview download failed: {e}")

            song_create = SongCreate(
                title=title,
                artist=artist,
                album=album,
                genre="Unknown",
                duration=duration,
                url=spotify_url,
                local_file_path=local_file_path,
                image_url=image_url,
            )

            created_song = SongService.create_song(db, song_create, user_id)
            created_songs.append(created_song)

        return created_songs
