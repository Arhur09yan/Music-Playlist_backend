"""
Script to create the playlist_songs table in the database if it does not exist.

Usage:
    docker compose exec api python scripts/add_playlist_songs_table.py
or:
    python scripts/add_playlist_songs_table.py
"""

import sys
import os

# Ensure app package is importable (when running from repo root on host)
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from sqlalchemy import text

from app.database import SessionLocal, engine


def create_playlist_songs_table() -> None:
    """Create playlist_songs table if it doesn't exist."""
    db = SessionLocal()
    try:
        # Detect database type from engine URL
        db_url = str(engine.url)
        is_postgres = db_url.startswith("postgresql")

        if is_postgres:
            # Check if table exists in Postgres
            check_query = text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE tablename = 'playlist_songs'
                """
            )
            result = db.execute(check_query).fetchone()
            if result:
                print("Table 'playlist_songs' already exists.")
                return

            # Create table
            create_query = text(
                """
                CREATE TABLE playlist_songs (
                    id SERIAL PRIMARY KEY,
                    playlist_id INTEGER REFERENCES playlists(id) ON DELETE CASCADE,
                    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
                    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                """
            )
            db.execute(create_query)
            db.commit()
            print("Successfully created 'playlist_songs' table (PostgreSQL).")
        else:
            # Fallback: generic CREATE TABLE IF NOT EXISTS (works for SQLite)
            create_query = text(
                """
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    song_id INTEGER,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            db.execute(create_query)
            db.commit()
            print("Successfully ensured 'playlist_songs' table exists (generic/SQLite).")

    except Exception as e:
        db.rollback()
        print(f"Error creating playlist_songs table: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_playlist_songs_table()


