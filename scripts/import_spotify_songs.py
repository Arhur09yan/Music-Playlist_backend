#!/usr/bin/env python3
"""
Script to import songs from Spotify into the database.
Usage: python scripts/import_spotify_songs.py "search query" [limit]
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.config import get_settings

# Load environment variables
settings = get_settings()


def import_songs(query: str, limit: int = 20):
    """Import songs from Spotify into the database"""
    # Check Spotify credentials
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        print("\n❌ ERROR: Spotify credentials not configured!")
        print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file")
        print("\nTo get credentials:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create an app")
        print("3. Copy Client ID and Client Secret to .env file")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        print(f"\n{'='*80}")
        print(f"Importing songs from Spotify: '{query}' (limit: {limit})")
        print(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'N/A'}")
        print(f"{'='*80}\n")
        
        songs = SpotifyService.import_songs_from_spotify(db, query, limit)
        
        print(f"\n{'='*80}")
        print(f"IMPORT COMPLETE!")
        print(f"{'='*80}")
        print(f"Total songs imported: {len(songs)}")
        print(f"\nImported songs:")
        for i, song in enumerate(songs, 1):
            print(f"  {i}. {song.title} - {song.artist} (ID: {song.id})")
        print(f"{'='*80}\n")
        
        return songs
    except Exception as e:
        print(f"\n❌ Error importing songs: {e}\n")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_spotify_songs.py 'search query' [limit]")
        print("\nExamples:")
        print("  python scripts/import_spotify_songs.py 'rock music' 20")
        print("  python scripts/import_spotify_songs.py 'jazz classics' 30")
        print("  python scripts/import_spotify_songs.py 'pop hits 2024' 50")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    import_songs(query, limit)


