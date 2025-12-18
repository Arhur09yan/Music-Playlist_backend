from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    # Denormalized album name for convenience/search
    album = Column(String, index=True)
    # Optional foreign key to Album
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True, index=True)
    genre = Column(String, index=True)
    duration = Column(Float)  # in seconds
    url = Column(String)  # Original preview URL from Spotify
    local_file_path = Column(String, nullable=True)  # Local cached file path
    image_url = Column(String, nullable=True)  # Album/cover image URL from Spotify
    liked = Column(Boolean, default=False, nullable=False)  # Liked status (defaults to False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    album_obj = relationship("Album", back_populates="songs")
    playlist_songs = relationship(
        "PlaylistSong", back_populates="song", cascade="all, delete-orphan"
    )
    likes = relationship("Like", back_populates="song", cascade="all, delete-orphan")

