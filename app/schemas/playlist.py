from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = ""

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PlaylistResponse(PlaylistBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlaylistDetailResponse(PlaylistResponse):
    songs: List['SongResponse'] = []

from app.schemas.song import SongResponse
PlaylistDetailResponse.model_rebuild()
