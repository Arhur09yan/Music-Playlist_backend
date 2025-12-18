from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.schemas.song import SongResponse


class AlbumBase(BaseModel):
    title: str
    artist: str
    image_url: Optional[str] = None
    description: Optional[str] = None


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class AlbumResponse(AlbumBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlbumDetailResponse(AlbumResponse):
    songs: List[SongResponse] = []


