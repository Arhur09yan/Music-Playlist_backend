from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.album import (
    AlbumCreate,
    AlbumResponse,
    AlbumDetailResponse,
    AlbumUpdate,
)
from app.schemas.song import SongResponse
from app.services.album_service import AlbumService
from app.utils.security import decode_token


router = APIRouter(prefix="/albums", tags=["albums"])
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return payload


@router.post("", response_model=AlbumResponse)
def create_album(
    album: AlbumCreate,
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    # We could associate albums with a user in the future using payload["sub"]
    return AlbumService.create_album(db, album)


@router.get("", response_model=List[AlbumResponse])
def get_albums(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return AlbumService.get_albums(db, skip, limit)


@router.get("/{album_id}", response_model=AlbumDetailResponse)
def get_album(album_id: int, db: Session = Depends(get_db)):
    album = AlbumService.get_album(db, album_id)
    # songs relationship is already loaded via AlbumService.get_album
    return album


@router.put("/{album_id}", response_model=AlbumResponse)
def update_album(
    album_id: int,
    album_update: AlbumUpdate,
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    return AlbumService.update_album(db, album_id, album_update)


@router.delete("/{album_id}")
def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    return AlbumService.delete_album(db, album_id)


@router.post("/{album_id}/songs/{song_id}", response_model=SongResponse)
def add_song_to_album(
    album_id: int,
    song_id: int,
    db: Session = Depends(get_db),
    payload=Depends(verify_token),
):
    """
    Attach an existing song to an album.
    """
    return AlbumService.add_song_to_album(db, album_id, song_id)


