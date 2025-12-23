#!/usr/bin/env python3
"""
Quick import script that uses minimal dependencies.
This script directly connects to the database and uses Spotify API.
"""
import sys
import os
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import declarative_base as old_declarative_base
from datetime import datetime

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://music_user:music_password@localhost:5433/music_db")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Load from .env file if it exists
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == "DATABASE_URL":
                    DATABASE_URL = value
                elif key == "SPOTIFY_CLIENT_ID":
                    SPOTIFY_CLIENT_ID = value
                elif key == "SPOTIFY_CLIENT_SECRET":
                    SPOTIFY_CLIENT_SECRET = value

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("❌ ERROR: Spotify credentials not found in .env file!")
    sys.exit(1)

# Database setup
Base = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    album = Column(String, index=True)
    genre = Column(String, index=True)
    duration = Column(Float)
    url = Column(String)
    local_file_path = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_spotify_token():
    """Get Spotify access token"""
    token_url = "https://accounts.spotify.com/api/token"
    response = requests.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]

def search_spotify(query, limit=20):
    """Search Spotify for tracks"""
    token = get_spotify_token()
    url = "https://api.spotify.com/v1/search"
    params = {"q": query, "type": "track", "limit": min(limit, 50)}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("tracks", {}).get("items", [])

def import_songs(query, limit=20):
    """Import songs from Spotify"""
    print(f"\n{'='*80}")
    print(f"Importing songs: '{query}' (limit: {limit})")
    print(f"{'='*80}\n")
    
    tracks = search_spotify(query, limit)
    if not tracks:
        print("❌ No tracks found!")
        return []
    
    db = SessionLocal()
    imported = []
    
    try:
        for track in tracks:
            title = track.get("name", "Unknown")
            artists = track.get("artists", [])
            artist = artists[0]["name"] if artists else "Unknown"
            album = track.get("album", {}).get("name", "Unknown")
            
            # Check if exists
            existing = db.query(Song).filter(
                Song.title == title,
                Song.artist == artist
            ).first()
            
            if existing:
                print(f"⏭️  Skipped (exists): {title} - {artist}")
                imported.append(existing)
                continue
            
            # Get URLs
            preview_url = track.get("preview_url", "")
            spotify_url = track.get("external_urls", {}).get("spotify", "")
            audio_url = preview_url or spotify_url
            
            # Get duration
            if preview_url:
                duration = 30.0
            else:
                duration_ms = track.get("duration_ms", 0)
                duration = duration_ms / 1000.0 if duration_ms > 0 else 0.0
            
            # Get image
            album_images = track.get("album", {}).get("images", [])
            image_url = album_images[0].get("url", "") if album_images else ""
            
            # Create song
            song = Song(
                title=title,
                artist=artist,
                album=album,
                genre="Unknown",
                duration=duration,
                url=audio_url,
                image_url=image_url
            )
            
            db.add(song)
            db.commit()
            db.refresh(song)
            imported.append(song)
            print(f"✅ Imported: {title} - {artist} (ID: {song.id})")
        
        print(f"\n{'='*80}")
        print(f"✅ IMPORT COMPLETE! Imported {len(imported)} songs")
        print(f"{'='*80}\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
    
    return imported

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/quick_import.py 'search query' [limit]")
        print("\nExamples:")
        print("  python scripts/quick_import.py 'popular music 2024' 30")
        print("  python scripts/quick_import.py 'rock music' 20")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    import_songs(query, limit)


