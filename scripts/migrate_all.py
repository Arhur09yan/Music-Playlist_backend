"""
Create all database tables defined by SQLAlchemy models (idempotent).

Usage:
    docker compose run --rm ... api python scripts/migrate_all.py
"""

import sys
import os

# Ensure repo root is on path so `app` package is importable
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.database import Base, engine

# Import models so they are registered with Base.metadata
from app.models import user, song, playlist, album  # noqa: F401


def run_migrations() -> None:
    """Create all tables based on SQLAlchemy models (no destructive changes)."""
    Base.metadata.create_all(bind=engine)
    print("✅ All SQLAlchemy models synced to database (create_all).")


if __name__ == "__main__":
    run_migrations()


