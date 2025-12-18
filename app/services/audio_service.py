import os
import hashlib
import logging
from pathlib import Path
from typing import Optional
import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioService:
    """Service for downloading and managing audio files from Spotify previews"""
    
    # Audio storage directory (relative to backend directory)
    # In Docker: /app/app/services/audio_service.py -> /app/audio_storage
    # The file is at app/services/audio_service.py, so we go up 3 levels to get to backend root
    _backend_root = Path(__file__).parent.parent.parent
    AUDIO_STORAGE_DIR = _backend_root / "audio_storage"
    
    @staticmethod
    def _ensure_storage_dir():
        """Create audio storage directory if it doesn't exist"""
        AudioService.AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        return AudioService.AUDIO_STORAGE_DIR
    
    @staticmethod
    def _get_file_hash(url: str) -> str:
        """Generate a hash from URL for unique filename"""
        return hashlib.md5(url.encode()).hexdigest()
    
    @staticmethod
    def _get_file_path(url: str) -> Path:
        """Get the local file path for a given URL"""
        AudioService._ensure_storage_dir()
        file_hash = AudioService._get_file_hash(url)
        return AudioService.AUDIO_STORAGE_DIR / f"{file_hash}.mp3"
    
    @staticmethod
    def download_preview(url: str) -> Optional[str]:
        """
        Download a Spotify preview URL and save it locally.
        Returns the local file path relative to backend directory, or None if download fails.
        """
        if not url:
            return None
        
        # Skip if it's not a preview URL (don't download full Spotify URLs)
        if not ("preview" in url or "p.scdn.co" in url or url.endswith(".mp3")):
            logger.warning(f"Skipping download for non-preview URL: {url}")
            return None
        
        file_path = AudioService._get_file_path(url)
        
        # If file already exists, return the path
        if file_path.exists():
            logger.info(f"Audio file already exists: {file_path.name}")
            relative_path = file_path.relative_to(AudioService._backend_root)
            return str(relative_path)
        
        try:
            logger.info(f"Downloading audio from: {url}")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check if response is actually audio
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("audio/"):
                logger.warning(f"Unexpected content type: {content_type} for URL: {url}")
                # Still try to save it, might be audio with wrong headers
            
            # Download and save file
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            logger.info(f"Downloaded audio file: {file_path.name} ({file_size} bytes)")
            
            # Return relative path from backend directory (for storage in DB)
            # This will be like "audio_storage/hash.mp3"
            relative_path = file_path.relative_to(AudioService._backend_root)
            logger.info(f"Returning relative path: {relative_path}")
            return str(relative_path)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download audio from {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            # Clean up partial file if it exists
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            return None
    
    @staticmethod
    def get_audio_path(url: str) -> Optional[str]:
        """
        Get the local file path for a preview URL.
        Downloads the file if it doesn't exist.
        Returns relative path from backend directory.
        """
        if not url:
            return None
        
        file_path = AudioService._get_file_path(url)
        
        # If file exists, return the path
        if file_path.exists():
            return str(file_path.relative_to(Path(__file__).parent.parent.parent))
        
        # Try to download it
        return AudioService.download_preview(url)
    
    @staticmethod
    def file_exists(url: str) -> bool:
        """Check if audio file has been downloaded"""
        if not url:
            return False
        file_path = AudioService._get_file_path(url)
        return file_path.exists()
    
    @staticmethod
    def delete_audio_file(url: str) -> bool:
        """Delete a downloaded audio file"""
        if not url:
            return False
        file_path = AudioService._get_file_path(url)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted audio file: {file_path.name}")
                return True
        except Exception as e:
            logger.error(f"Error deleting audio file: {str(e)}")
        return False

