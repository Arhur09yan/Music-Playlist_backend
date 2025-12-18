from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    image_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    songs = relationship(
        "Song",
        back_populates="album_obj",
        cascade="all, delete-orphan",
    )


