# services/api_service/src/api_service/routers/import_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
import re
from redis import Redis
from rq import Queue
from shared.config import REDIS_URL

router = APIRouter()

#connect to redis and create queue
redis_conn = Redis.from_url(REDIS_URL)
q = Queue("default", connection=redis_conn)

class ImportRequest(BaseModel):
    folder_id: Optional[str] = None
    folder_url: Optional[str] = None

    @validator("folder_id", "folder_url", pre=True)
    def empty_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

def extract_folder_id_from_url(url: str) -> Optional[str]:
    m = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    return None


# def _call_worker(folder_id: str):
#     # Import inside function to avoid circular imports at module import time
#     from services.worker_service.src.worker_service.tasks import import_images_from_drive
#     return import_images_from_drive(folder_id)


@router.post("/import/google-drive")
def import_google_drive(req: ImportRequest):
    """
    Enqueue an image import job to the Redis queue.
    The worker service will process it asynchronously.
    """
    folder_id = req.folder_id
    if not folder_id and req.folder_url:
        folder_id = extract_folder_id_from_url(req.folder_url)
    if not folder_id:
        raise HTTPException(status_code=400, detail="folder_id or valid folder_url required")
    
    
    job = q.enqueue("services.worker_service.src.tasks.import_images_from_drive", folder_id)
    return {
        "message": "Import started in background",
        "folder_id": folder_id,
        "job_id": job.id
    }
