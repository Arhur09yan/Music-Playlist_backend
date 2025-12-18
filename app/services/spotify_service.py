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
    @staticmethod
    def _get_access_token() -> str:
        client_id = settings.SPOTIFY_CLIENT_ID
        client_secret = settings.SPOTIFY_CLIENT_SECRET

        if not client_id or not client_secret:
            raise ValueError("Spotify client credentials are not configured")

        token_url = "https://accounts.spotify.com/api/token"
        response = requests.post(
            token_url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Spotify access token obtained: {data.get('token_type', 'N/A')}")
        return data["access_token"]

    @staticmethod
    def _search_track_raw(query: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        access_token = SpotifyService._get_access_token()
        url = "https://api.spotify.com/v1/search"
        params = {"q": query, "type": "track", "limit": limit}
        headers = {"Authorization": f"Bearer {access_token}"}

        logger.info(f"Searching Spotify for: {query} (limit: {limit})")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Spotify API HTTP error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Spotify API error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API request error: {str(e)}")
            raise ValueError(f"Failed to connect to Spotify API: {str(e)}")

        # Print the full Spotify response
        print("\n" + "="*80)
        print("SPOTIFY API RESPONSE:")
        print("="*80)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        items = data.get("tracks", {}).get("items", [])
        if not items:
            logger.warning(f"No tracks found for query: {query}")
            return None

        # Prefer a track that has a preview_url so we can play it in the app
        track_with_preview = next(
            (item for item in items if item.get("preview_url")), None
        )
        track = track_with_preview or items[0]

        logger.info(f"Found track: {track.get('name', 'Unknown')} by {track.get('artists', [{}])[0].get('name', 'Unknown')}")
        return track

    @staticmethod
    def _search_tracks_raw(query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for multiple tracks on Spotify"""
        access_token = SpotifyService._get_access_token()
        url = "https://api.spotify.com/v1/search"
        params = {"q": query, "type": "track", "limit": min(limit, 50)}  # Spotify max is 50
        headers = {"Authorization": f"Bearer {access_token}"}

        logger.info(f"Searching Spotify for multiple tracks: {query} (limit: {limit})")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Spotify API HTTP error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Spotify API error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API request error: {str(e)}")
            raise ValueError(f"Failed to connect to Spotify API: {str(e)}")

        # Print the full Spotify response
        print("\n" + "="*80)
        print("SPOTIFY API RESPONSE (BULK SEARCH):")
        print("="*80)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        items = data.get("tracks", {}).get("items", [])

        # Import all tracks, not just those with preview_url
        # Tracks with preview_url can be played in-app, others will use Spotify URL
        items_with_preview = [item for item in items if item.get("preview_url")]
        logger.info(
            f"Found {len(items)} tracks for query: {query}, "
            f"{len(items_with_preview)} with preview_url"
        )
        
        # Print summary of found tracks
        if items:
            print("\n" + "-"*80)
            print("FOUND TRACKS SUMMARY:")
            print("-"*80)
            for i, track in enumerate(items, 1):
                artists = track.get("artists", [])
                artist_names = ", ".join([a.get("name", "Unknown") for a in artists])
                has_preview = "✓" if track.get("preview_url") else "✗"
                print(f"{i}. {track.get('name', 'Unknown')} - {artist_names} [Preview: {has_preview}]")
                print(f"   Album: {track.get('album', {}).get('name', 'Unknown')}")
                print(f"   Duration: {track.get('duration_ms', 0) / 1000:.2f}s")
                print(f"   Spotify URL: {track.get('external_urls', {}).get('spotify', 'N/A')}")
            print("-"*80 + "\n")
        
        return items

    @staticmethod
    def import_song_from_spotify(db: Session, query: str, user_id: Optional[int] = None) -> Optional[SongResponse]:
        """
        Search for a track on Spotify by query, map it into our Song schema,
        store it in the database, and return the created Song with liked status.
        """
        track = SpotifyService._search_track_raw(query)
        if not track:
            return None

        # Print track data before processing
        print("\n" + "="*80)
        print("PROCESSING TRACK DATA:")
        print("="*80)
        print(json.dumps(track, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        title = track.get("name", "Unknown Title")
        artists = track.get("artists", [])
        artist_name = artists[0]["name"] if artists else "Unknown Artist"
        album = track.get("album", {}).get("name", "Unknown Album")
        
        external_urls = track.get("external_urls", {})
        spotify_url = external_urls.get("spotify", "")
        preview_url = track.get("preview_url", "")  # 30-second preview from Spotify
        
        # Use preview URL if available, otherwise use Spotify URL
        # If preview exists, set duration to 30 seconds; otherwise use full track duration
        if preview_url:
            duration_seconds = 30.0  # Preview length
            audio_url = preview_url
        else:
            duration_ms = track.get("duration_ms", 0)
            duration_seconds = duration_ms / 1000.0 if duration_ms > 0 else 0.0
            audio_url = spotify_url  # Fallback to Spotify URL
            logger.info(f"Song '{title}' has no preview URL, using Spotify URL instead")

        genres = []  # Track objects usually don't include genres directly
        genre = genres[0] if genres else "Unknown"
        
        # Get album image
        album_data = track.get("album", {})
        album_images = album_data.get("images", [])
        album_image_url = album_images[0].get("url", "") if album_images else ""

        # Print mapped song data
        print("\n" + "-"*80)
        print("MAPPED SONG DATA:")
        print("-"*80)
        print(f"Title: {title}")
        print(f"Artist: {artist_name}")
        print(f"Album: {album}")
        print(f"Genre: {genre}")
        print(f"Duration: {duration_seconds:.2f}s (30s preview)")
        print(f"Spotify URL: {spotify_url}")
        print(f"Preview URL: {preview_url}")
        print(f"Album Image: {album_image_url or 'Not available'}")
        print("-"*80 + "\n")

        # Download preview audio file only if preview URL exists
        local_file_path = None
        if preview_url:
            local_file_path = AudioService.download_preview(preview_url)
            if local_file_path:
                logger.info(f"Downloaded audio file: {local_file_path}")
            else:
                logger.warning(f"Failed to download audio for: {title}")

        # Store URL (preview or Spotify) and local file path for audio playback
        song_create = SongCreate(
            title=title,
            artist=artist_name,
            album=album,
            genre=genre,
            duration=duration_seconds,
            url=audio_url,  # Preview URL if available, otherwise Spotify URL
            local_file_path=local_file_path,  # Local cached file path (only if preview exists)
            image_url=album_image_url,  # Album cover image from Spotify
        )

        created_song = SongService.create_song(db, song_create, user_id)
        logger.info(f"Song imported successfully: {created_song.id} - {title}")
        return created_song

    @staticmethod
    def import_songs_from_spotify(db: Session, query: str, limit: int = 20, user_id: Optional[int] = None) -> List[SongResponse]:
        """
        Search for multiple tracks on Spotify by query, map them into our Song schema,
        store them in the database, and return the created Songs with liked status.
        """
        tracks = SpotifyService._search_tracks_raw(query, limit)
        if not tracks:
            return []

        created_songs = []
        for track in tracks:
            # Check if song already exists (by title and artist to avoid duplicates)
            title = track.get("name", "Unknown Title")
            artists = track.get("artists", [])
            artist_name = artists[0]["name"] if artists else "Unknown Artist"
            
            # Check for duplicates
            existing = db.query(Song).filter(
                Song.title == title,
                Song.artist == artist_name
            ).first()
            
            if existing:
                # Update existing song if it's missing image_url
                album_data = track.get("album", {})
                album_images = album_data.get("images", [])
                album_image_url = album_images[0].get("url", "") if album_images else ""
                
                if not existing.image_url and album_image_url:
                    existing.image_url = album_image_url
                    db.commit()
                    db.refresh(existing)
                    logger.info(f"Updated image_url for existing song: {title}")
                
                # Convert existing Song to SongResponse with liked status
                from app.schemas.song import SongResponse
                liked = False
                if user_id is not None:
                    from app.models.playlist import Like
                    liked = db.query(Like).filter(
                        (Like.user_id == user_id) & (Like.song_id == existing.id)
                    ).first() is not None
                
                song_dict = {
                    "id": existing.id,
                    "title": existing.title,
                    "artist": existing.artist,
                    "album": existing.album,
                    "genre": existing.genre,
                    "duration": existing.duration,
                    "url": existing.url,
                    "local_file_path": existing.local_file_path,
                    "album_id": existing.album_id,
                    "image_url": existing.image_url,
                    "created_at": existing.created_at,
                    "liked": liked
                }
                created_songs.append(SongResponse(**song_dict))
                continue

            album = track.get("album", {}).get("name", "Unknown Album")
            preview_url = track.get("preview_url", "")  # 30-second preview from Spotify
            
            # Get Spotify URL
            external_urls = track.get("external_urls", {})
            spotify_url = external_urls.get("spotify", "")
            
            # Use preview URL if available, otherwise use Spotify URL
            # If preview exists, set duration to 30 seconds; otherwise use full track duration
            if preview_url:
                duration_seconds = 30.0  # Preview length
                audio_url = preview_url
            else:
                duration_ms = track.get("duration_ms", 0)
                duration_seconds = duration_ms / 1000.0 if duration_ms > 0 else 0.0
                audio_url = spotify_url  # Fallback to Spotify URL
                logger.info(f"Song '{title}' by '{artist_name}' has no preview URL, using Spotify URL instead")

            genres = []  # Track objects usually don't include genres directly
            genre = genres[0] if genres else "Unknown"
            
            # Get album image
            album_data = track.get("album", {})
            album_images = album_data.get("images", [])
            album_image_url = album_images[0].get("url", "") if album_images else ""

            # Download preview audio file only if preview URL exists
            local_file_path = None
            if preview_url:
                local_file_path = AudioService.download_preview(preview_url)
                if local_file_path:
                    logger.info(f"Downloaded audio file: {local_file_path}")
                else:
                    logger.warning(f"Failed to download audio for: {title}")

            # Store URL (preview or Spotify) and local file path for audio playback
            song_create = SongCreate(
                title=title,
                artist=artist_name,
                album=album,
                genre=genre,
                duration=duration_seconds,
                url=audio_url,  # Preview URL if available, otherwise Spotify URL
                local_file_path=local_file_path,  # Local cached file path (only if preview exists)
                image_url=album_image_url,  # Album cover image from Spotify
            )

            created_song = SongService.create_song(db, song_create, user_id)
            created_songs.append(created_song)

        return created_songs


