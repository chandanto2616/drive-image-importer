from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    google_drive_id = Column(String, unique=True, index=True)
    size = Column(BigInteger, nullable=True)
    mime_type = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)
    public_url = Column(String, nullable=True)  # New column for public URL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Pydantic schema for API responses
class ImageSchema(BaseModel):
    id: int
    name: str
    google_drive_id: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    storage_path: str
    public_url: Optional[str] = None  # Include in API response
    created_at: Optional[str] = None  # ISO string from DB

    class Config:
        from_attributes = True
