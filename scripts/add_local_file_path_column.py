#!/usr/bin/env python3
"""
Migration script to add local_file_path column to songs table.
Run this script to update existing database schema.

Usage:
    docker compose exec api python -c "
    from sqlalchemy import text
    from app.database import engine
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE songs ADD COLUMN IF NOT EXISTS local_file_path VARCHAR'))
        conn.commit()
    print('Migration completed!')
    "

Or use the direct SQL command:
    docker compose exec db psql -U music_user -d music_db -c "ALTER TABLE songs ADD COLUMN IF NOT EXISTS local_file_path VARCHAR;"
"""

