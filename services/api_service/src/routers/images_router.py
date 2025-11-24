from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.models import Image
from ..dependencies import get_db

router = APIRouter()

@router.get("/images")
def list_images(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    total = db.query(Image).count()
    rows = db.query(Image).offset(offset).limit(limit).all()

    items = [
        {
            "id": img.id,
            "name": img.name,
            "google_drive_id": img.google_drive_id,
            "size": img.size,
            "mime_type": img.mime_type,
            "storage_path": img.storage_path,
            "url": img.public_url,  # use the Cloudinary URL from DB
        }
        for img in rows
    ]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }
