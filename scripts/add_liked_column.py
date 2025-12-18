"""
Script to add 'liked' column to songs table.
This column will default to False for all existing songs.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from sqlalchemy import text

def add_liked_column():
    """Add liked column to songs table if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='songs' AND column_name='liked'
        """)
        result = db.execute(check_query).fetchone()
        
        if result:
            print("Column 'liked' already exists in songs table.")
            return
        
        # Add the column
        alter_query = text("""
            ALTER TABLE songs 
            ADD COLUMN liked BOOLEAN NOT NULL DEFAULT FALSE
        """)
        db.execute(alter_query)
        db.commit()
        print("Successfully added 'liked' column to songs table with default value False.")
        
    except Exception as e:
        db.rollback()
        print(f"Error adding liked column: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_liked_column()

