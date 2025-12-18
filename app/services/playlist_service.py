from sqlalchemy.orm import Session, joinedload
from app.models.playlist import Playlist, PlaylistSong, Like
from app.models.song import Song
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate
from app.schemas.song import SongCreate, SongResponse
from app.services.song_service import SongService
from fastapi import HTTPException, status

class PlaylistService:
    @staticmethod
    def create_playlist(db: Session, playlist_create: PlaylistCreate, user_id: int) -> Playlist:
        db_playlist = Playlist(
            name=playlist_create.name,
            description=playlist_create.description,
            owner_id=user_id
        )
        db.add(db_playlist)
        db.commit()
        db.refresh(db_playlist)
        return db_playlist

    @staticmethod
    def get_user_playlists(db: Session, user_id: int, skip: int = 0, limit: int = 20):
        return db.query(Playlist).filter(Playlist.owner_id == user_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_playlist(db: Session, playlist_id: int) -> Playlist:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found"
            )
        return playlist

    @staticmethod
    def update_playlist(db: Session, playlist_id: int, playlist_update: PlaylistUpdate, user_id: int) -> Playlist:
        playlist = PlaylistService.get_playlist(db, playlist_id)
        
        if playlist.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this playlist"
            )
        
        update_data = playlist_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(playlist, field, value)
        db.commit()
        db.refresh(playlist)
        return playlist

    @staticmethod
    def delete_playlist(db: Session, playlist_id: int, user_id: int):
        playlist = PlaylistService.get_playlist(db, playlist_id)
        
        if playlist.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this playlist"
            )
        
        db.delete(playlist)
        db.commit()
        return {"message": "Playlist deleted successfully"}

    @staticmethod
    def add_song_to_playlist(db: Session, playlist_id: int, song_id: int, user_id: int):
        playlist = PlaylistService.get_playlist(db, playlist_id)
        
        if playlist.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this playlist"
            )
        
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        # Check if song already in playlist
        existing = db.query(PlaylistSong).filter(
            (PlaylistSong.playlist_id == playlist_id) & (PlaylistSong.song_id == song_id)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Song already in playlist"
            )
        
        playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
        db.add(playlist_song)
        db.commit()
        db.refresh(playlist)
        return playlist

    @staticmethod
    def remove_song_from_playlist(db: Session, playlist_id: int, song_id: int, user_id: int):
        playlist = PlaylistService.get_playlist(db, playlist_id)
        
        if playlist.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this playlist"
            )
        
        playlist_song = db.query(PlaylistSong).filter(
            (PlaylistSong.playlist_id == playlist_id) & (PlaylistSong.song_id == song_id)
        ).first()
        
        if not playlist_song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not in playlist"
            )
        
        db.delete(playlist_song)
        db.commit()
        return {"message": "Song removed from playlist"}

class LikeService:
    @staticmethod
    def _add_liked_status(song: Song, user_id: int, db: Session) -> SongResponse:
        """
        Helper function to add liked status to a song and return SongResponse.
        If song is None or doesn't exist, liked will be False.
        """
        if song is None:
            raise ValueError("Song cannot be None")
        
        # Check if user has liked this song
        # If song was deleted, likes are automatically deleted (cascade), so this will return False
        like_exists = db.query(Like).filter(
            (Like.user_id == user_id) & (Like.song_id == song.id)
        ).first() is not None
        
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
            "liked": like_exists  # Explicitly set liked field
        }
        return SongResponse(**song_dict)
    
    @staticmethod
    def like_song(db: Session, song_id: int, user_id: int):
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        existing_like = db.query(Like).filter(
            (Like.user_id == user_id) & (Like.song_id == song_id)
        ).first()
        
        if existing_like:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Song already liked"
            )
        
        like = Like(user_id=user_id, song_id=song_id)
        db.add(like)
        
        # Update the liked column in songs table to True
        song.liked = True
        db.add(song)  # Ensure song is in the session
        db.commit()
        db.refresh(song)
        
        # Return song with liked=True
        return LikeService._add_liked_status(song, user_id, db)
    
    @staticmethod
    def like_song_with_data(db: Session, song_data: SongCreate, user_id: int):
        """
        Like a song by providing full song data.
        If the song doesn't exist in the database, it will be created first.
        Returns the full song data with all fields (title, artist, album, etc.)
        """
        # Check if song already exists (by title and artist to avoid duplicates)
        existing_song = db.query(Song).filter(
            (Song.title == song_data.title) & (Song.artist == song_data.artist)
        ).first()
        
        if existing_song:
            # Song exists, use it
            song = existing_song
        else:
            # Song doesn't exist, create it (returns SongResponse, but we need Song model)
            song_response = SongService.create_song(db, song_data, user_id)
            # Get the Song model from database
            song = db.query(Song).filter(Song.id == song_response.id).first()
            if not song:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create song"
                )
        
        # Check if already liked
        existing_like = db.query(Like).filter(
            (Like.user_id == user_id) & (Like.song_id == song.id)
        ).first()
        
        if existing_like:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Song already liked"
            )
        
        # Create the like
        like = Like(user_id=user_id, song_id=song.id)
        db.add(like)
        
        # Update the liked column in songs table to True
        song.liked = True
        db.add(song)  # Ensure song is in the session
        db.commit()
        db.refresh(song)
        
        # Return full song data with liked=True
        return LikeService._add_liked_status(song, user_id, db)

    @staticmethod
    def unlike_song(db: Session, song_id: int, user_id: int):
        like = db.query(Like).filter(
            (Like.user_id == user_id) & (Like.song_id == song_id)
        ).first()
        
        if not like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found"
            )
        
        # Remove the like from likes table
        db.delete(like)
        
        # Note: We do NOT change the liked column in songs table
        # Once liked=True, it stays True (one-way flag)
        # The likes table tracks which users have liked the song
        
        db.commit()
        return {"message": "Song unliked"}

    @staticmethod
    def get_user_likes(db: Session, user_id: int, skip: int = 0, limit: int = 20):
        """
        Get all songs liked by the user.
        Only returns songs that still exist in the database.
        If a song was deleted, its likes are automatically removed (cascade delete),
        so deleted songs won't appear in this list.
        All returned songs will have liked=True.
        """
        # Eagerly load song relationship with all fields (title, artist, album, etc.)
        # Filter out any likes where the song might have been deleted
        likes = db.query(Like).options(
            joinedload(Like.song)
        ).filter(
            Like.user_id == user_id
        ).order_by(Like.created_at.desc()).offset(skip).limit(limit).all()
        
        # Extract songs with full data and add liked=True for all (since they're from user's likes)
        # Filter out None songs (shouldn't happen with cascade, but safety check)
        songs = [LikeService._add_liked_status(like.song, user_id, db) for like in likes if like.song is not None]
        return songs
