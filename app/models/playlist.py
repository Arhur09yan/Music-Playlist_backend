from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, default="")
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="playlists")
    songs = relationship("PlaylistSong", back_populates="playlist", cascade="all, delete-orphan")

class PlaylistSong(Base):
    __tablename__ = "playlist_songs"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))
    added_at = Column(DateTime, default=datetime.utcnow)

    playlist = relationship("Playlist", back_populates="songs")
    song = relationship("Song", back_populates="playlist_songs")

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="likes")
    song = relationship("Song", back_populates="likes")
