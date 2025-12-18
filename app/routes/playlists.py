from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.playlist import PlaylistCreate, PlaylistResponse, PlaylistDetailResponse, PlaylistUpdate
from app.services.playlist_service import PlaylistService
from app.utils.security import decode_token
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from typing import List

router = APIRouter(prefix="/playlists", tags=["playlists"])
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return payload

@router.post("", response_model=PlaylistResponse)
def create_playlist(playlist: PlaylistCreate, db: Session = Depends(get_db), payload = Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return PlaylistService.create_playlist(db, playlist, user_id)

@router.get("", response_model=List[PlaylistResponse])
def get_user_playlists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    payload = Depends(verify_token)
):
    user_id = int(payload.get("sub"))
    return PlaylistService.get_user_playlists(db, user_id, skip, limit)

@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    return PlaylistService.get_playlist(db, playlist_id)

@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(playlist_id: int, playlist_update: PlaylistUpdate, db: Session = Depends(get_db), payload = Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return PlaylistService.update_playlist(db, playlist_id, playlist_update, user_id)

@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db), payload = Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return PlaylistService.delete_playlist(db, playlist_id, user_id)

@router.post("/{playlist_id}/songs/{song_id}")
def add_song_to_playlist(playlist_id: int, song_id: int, db: Session = Depends(get_db), payload = Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return PlaylistService.add_song_to_playlist(db, playlist_id, song_id, user_id)

@router.delete("/{playlist_id}/songs/{song_id}")
def remove_song_from_playlist(playlist_id: int, song_id: int, db: Session = Depends(get_db), payload = Depends(verify_token)):
    user_id = int(payload.get("sub"))
    return PlaylistService.remove_song_from_playlist(db, playlist_id, song_id, user_id)
