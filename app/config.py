from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    # Default to PostgreSQL for local development (localhost:5433), but can be overridden via .env
    # For Docker containers, use: postgresql+psycopg2://music_user:music_password@db:5432/music_db
    DATABASE_URL: str = "postgresql+psycopg2://music_user:music_password@localhost:5433/music_db"
    
    # Spotify API
    SPOTIFY_CLIENT_ID: str | None = None
    SPOTIFY_CLIENT_SECRET: str | None = None
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Server
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # CORS
    ALLOWED_ORIGINS: str = "*"  # Comma-separated list of allowed origins
    
    # Audio Storage
    AUDIO_STORAGE_DIR: str = "audio_storage"  # Directory for cached audio files
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Environment variables take precedence over .env file
        case_sensitive = False

@lru_cache
def get_settings():
    return Settings()
