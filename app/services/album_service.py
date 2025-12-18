from typing import List

from sqlalchemy.orm import Session

from app.models.album import Album
from app.models.song import Song
from app.schemas.album import AlbumCreate, AlbumUpdate
from fastapi import HTTPException, status


class AlbumService:
    @staticmethod
    def create_album(db: Session, album_create: AlbumCreate) -> Album:
        db_album = Album(**album_create.model_dump())
        db.add(db_album)
        db.commit()
        db.refresh(db_album)
        return db_album

    @staticmethod
    def get_albums(db: Session, skip: int = 0, limit: int = 20) -> List[Album]:
        return db.query(Album).offset(skip).limit(limit).all()

    @staticmethod
    def get_album(db: Session, album_id: int) -> Album:
        album = db.query(Album).filter(Album.id == album_id).first()
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album not found",
            )
        # Ensure songs relationship is loaded if needed
        _ = album.songs  # access to trigger lazy load if configured
        return album

    @staticmethod
    def update_album(
        db: Session, album_id: int, album_update: AlbumUpdate
    ) -> Album:
        album = AlbumService.get_album(db, album_id)
        update_data = album_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(album, field, value)
        db.commit()
        db.refresh(album)
        return album

    @staticmethod
    def delete_album(db: Session, album_id: int):
        album = AlbumService.get_album(db, album_id)
        db.delete(album)
        db.commit()
        return {"message": "Album deleted successfully"}

    @staticmethod
    def add_song_to_album(db: Session, album_id: int, song_id: int) -> Song:
        album = AlbumService.get_album(db, album_id)
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found",
            )

        song.album_id = album.id
        # keep denormalized album name in song.album as well
        song.album = album.title
        db.commit()
        db.refresh(song)
        return song

