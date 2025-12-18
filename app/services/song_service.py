from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.song import Song
from app.models.playlist import Like
from app.schemas.song import SongCreate, SongUpdate, SongResponse
from fastapi import HTTPException, status

class SongService:
    @staticmethod
    def create_song(db: Session, song_create: SongCreate, user_id: Optional[int] = None) -> SongResponse:
        """Create a song and return with liked status."""
        db_song = Song(**song_create.model_dump())
        db.add(db_song)
        db.commit()
        db.refresh(db_song)
        
        # Check if user liked this song (should be False for new song, but check anyway)
        liked = False
        if user_id is not None:
            liked = db.query(Like).filter(
                (Like.user_id == user_id) & (Like.song_id == db_song.id)
            ).first() is not None
        
        # Create SongResponse with explicit liked field
        song_dict = {
            "id": db_song.id,
            "title": db_song.title,
            "artist": db_song.artist,
            "album": db_song.album,
            "genre": db_song.genre,
            "duration": db_song.duration,
            "url": db_song.url,
            "local_file_path": db_song.local_file_path,
            "album_id": db_song.album_id,
            "image_url": db_song.image_url,
            "created_at": db_song.created_at,
            "liked": liked  # Explicitly set liked field
        }
        return SongResponse(**song_dict)

    @staticmethod
    def get_all_songs(db: Session, skip: int = 0, limit: int = 20, user_id: Optional[int] = None) -> List[SongResponse]:
        """Get all songs with liked status. If user_id is provided, checks if user liked each song."""
        songs = db.query(Song).order_by(Song.id.asc()).offset(skip).limit(limit).all()
        
        # Get all song IDs that have likes (any user) for efficiency
        songs_with_likes = {like.song_id for like in db.query(Like.song_id).distinct().all()}
        
        # Get all song IDs that user has liked (for efficiency) if user_id provided
        user_liked_song_ids = set()
        if user_id is not None:
            user_liked_song_ids = {like.song_id for like in db.query(Like).filter(Like.user_id == user_id).all()}
        
        # Create SongResponse with explicit liked field
        result = []
        for song in songs:
            # Check if song has any likes in the likes table
            # If user_id provided, also check if this specific user liked it
            if user_id is not None:
                # User-specific: check if this user liked the song
                liked_status = song.id in user_liked_song_ids
            else:
                # No user: check if song has any likes (any user)
                liked_status = song.id in songs_with_likes
            
            # Convert song to dict and add liked field
            song_dict = {
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "genre": song.genre,
                "duration": song.duration,
                "url": song.url,
                "local_file_path": song.local_file_path,
                "album_id": song.album_id,
                "image_url": song.image_url,
                "created_at": song.created_at,
                "liked": liked_status
            }
            song_data = SongResponse(**song_dict)
            result.append(song_data)
        
        return result

    @staticmethod
    def get_song(db: Session, song_id: int, user_id: Optional[int] = None) -> SongResponse:
        """Get a song by ID with liked status. If user_id is provided, checks if user liked the song."""
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        # Check if song has any likes in the likes table
        # If user_id provided, check if this specific user liked it
        if user_id is not None:
            # User-specific: check if this user liked the song
            liked = db.query(Like).filter(
                (Like.user_id == user_id) & (Like.song_id == song_id)
            ).first() is not None
        else:
            # No user: check if song has any likes (any user)
            liked = db.query(Like).filter(Like.song_id == song_id).first() is not None
        
        # Create SongResponse with explicit liked field
        song_dict = {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "album": song.album,
            "genre": song.genre,
            "duration": song.duration,
            "url": song.url,
            "local_file_path": song.local_file_path,
            "album_id": song.album_id,
            "image_url": song.image_url,
            "created_at": song.created_at,
            "liked": liked
        }
        return SongResponse(**song_dict)

    @staticmethod
    def update_song(db: Session, song_id: int, song_update: SongUpdate, user_id: Optional[int] = None) -> SongResponse:
        """Update a song and return with liked status."""
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        update_data = song_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(song, field, value)
        db.commit()
        db.refresh(song)
        
        # Check if song has any likes in the likes table
        # If user_id provided, check if this specific user liked it
        if user_id is not None:
            # User-specific: check if this user liked the song
            liked = db.query(Like).filter(
                (Like.user_id == user_id) & (Like.song_id == song_id)
            ).first() is not None
        else:
            # No user: check if song has any likes (any user)
            liked = db.query(Like).filter(Like.song_id == song_id).first() is not None
        
        # Create SongResponse with explicit liked field
        song_dict = {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "album": song.album,
            "genre": song.genre,
            "duration": song.duration,
            "url": song.url,
            "local_file_path": song.local_file_path,
            "album_id": song.album_id,
            "image_url": song.image_url,
            "created_at": song.created_at,
            "liked": liked  # Use database column or user-specific check
        }
        return SongResponse(**song_dict)

    @staticmethod
    def delete_song(db: Session, song_id: int):
        """
        Delete a song from the database.
        This will also automatically delete all associated likes due to cascade delete.
        All likes for this song will be removed, effectively setting liked=false for all users.
        """
        song = SongService.get_song(db, song_id)
        
        # Count likes before deletion (for response message)
        likes_count = db.query(Like).filter(Like.song_id == song_id).count()
        
        # Delete the song (cascade will automatically delete all associated likes)
        db.delete(song)
        db.commit()
        
        return {
            "message": f"Song deleted successfully",
            "deleted_likes_count": likes_count,
            "song_id": song_id,
            "song_title": song.title,
            "song_artist": song.artist
        }

    @staticmethod
    def search_songs(db: Session, q: str, skip: int = 0, limit: int = 20, user_id: Optional[int] = None) -> List[SongResponse]:
        """Search songs with liked status. If user_id is provided, checks if user liked each song."""
        query = db.query(Song).filter(
            or_(
                Song.title.ilike(f"%{q}%"),
                Song.artist.ilike(f"%{q}%"),
                Song.album.ilike(f"%{q}%"),
                Song.genre.ilike(f"%{q}%")
            )
        )
        songs = query.order_by(Song.id.asc()).offset(skip).limit(limit).all()
        
        # Get all song IDs that have likes (any user) for efficiency
        songs_with_likes = {like.song_id for like in db.query(Like.song_id).distinct().all()}
        
        # Get all song IDs that user has liked (for efficiency) if user_id provided
        user_liked_song_ids = set()
        if user_id is not None:
            user_liked_song_ids = {like.song_id for like in db.query(Like).filter(Like.user_id == user_id).all()}
        
        # Create SongResponse with explicit liked field
        result = []
        for song in songs:
            # Check if song has any likes in the likes table
            # If user_id provided, also check if this specific user liked it
            if user_id is not None:
                # User-specific: check if this user liked the song
                liked_status = song.id in user_liked_song_ids
            else:
                # No user: check if song has any likes (any user)
                liked_status = song.id in songs_with_likes
            
            song_dict = {
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "genre": song.genre,
                "duration": song.duration,
                "url": song.url,
                "local_file_path": song.local_file_path,
                "album_id": song.album_id,
                "image_url": song.image_url,
                "created_at": song.created_at,
                "liked": liked_status
            }
            song_data = SongResponse(**song_dict)
            result.append(song_data)
        
        return result

    @staticmethod
    def get_song_count(db: Session):
        return db.query(Song).count()
