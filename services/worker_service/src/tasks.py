import os
import io
import json
import logging
import traceback
import concurrent.futures
from typing import List, Dict, Optional
from rq import get_current_job
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.config import SERVICE_ACCOUNT_JSON
from shared.cloudinary_client import upload_file
from shared.models import Image
from shared.database import get_db_session, init_db

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(name)s: %(message)s")


def get_drive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("SERVICE_ACCOUNT_JSON is not set in environment variables")

    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    logger.info("✅ Google Drive service initialized")
    return service


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_single_file(service, file_data: Dict) -> Dict:
    from googleapiclient.http import MediaIoBaseDownload
    import socket

    file_id = file_data["id"]
    file_name = file_data["name"]
    mime_type = file_data.get("mimeType")
    size = int(file_data.get("size")) if file_data.get("size") else None

    buffer = io.BytesIO()
    request = service.files().get_media(fileId=file_id)
    downloader = MediaIoBaseDownload(buffer, request, chunksize=512 * 1024)
    done = False

    socket.setdefaulttimeout(600)
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    logger.info(f"✅ Downloaded {file_name} ({len(buffer.getvalue())} bytes)")

    public_url = upload_file(buffer, file_name, content_type=mime_type)
    logger.info(f"✅ Uploaded {file_name} to Cloudinary at {public_url}")

    return {
        "status": "success",
        "file_id": file_id,
        "file_name": file_name,
        "mime_type": mime_type,
        "size": size,
        "public_url": public_url
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=5))
def download_and_upload_to_cloudinary(folder_id: str, max_workers: int = 1) -> List[Dict]:
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    page_token: Optional[str] = None
    all_files: List[Dict] = []

    while True:
        results = service.files().list(
            q=query,
            pageSize=1000,
            pageToken=page_token,
            corpora="allDrives",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="nextPageToken, files(id, name, mimeType, size)"
        ).execute()

        files = results.get("files", [])
        all_files.extend(files)
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    if not all_files:
        logger.warning("⚠️ No image files found in the folder")
        return []

    uploaded: List[Dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_single_file, service, f): f for f in all_files}
        for future in concurrent.futures.as_completed(future_to_file):
            file_data = future_to_file[future]
            try:
                result = future.result()
                if result["status"] == "success":
                    uploaded.append(result)
            except Exception as e:
                logger.error(f"❌ Failed processing {file_data['name']}: {str(e)}")
                logger.error(traceback.format_exc())

    logger.info(f"✅ Uploaded {len(uploaded)}/{len(all_files)} files successfully")
    return uploaded


def import_images_from_drive(folder_id: str) -> dict:
    job = get_current_job()
    job_id = job.id if job else None
    logger.info(f"🚀 Starting import job for folder {folder_id} (Job ID: {job_id})")

    db = None
    try:
        init_db()
        db = get_db_session()
        files = download_and_upload_to_cloudinary(folder_id, max_workers=1)

        imported = updated = 0
        for f in files:
            existing = db.query(Image).filter_by(google_drive_id=f["file_id"]).first()
            if existing:
                existing.name = f["file_name"]
                existing.size = f["size"]
                existing.mime_type = f["mime_type"]
                existing.storage_path = f["file_name"]
                existing.public_url = f["public_url"]
                db.commit()
                db.refresh(existing)
                updated += 1
            else:
                img = Image(
                    name=f["file_name"],
                    google_drive_id=f["file_id"],
                    size=f["size"],
                    mime_type=f["mime_type"],
                    storage_path=f["file_name"],
                    public_url=f["public_url"]
                )
                db.add(img)
                db.commit()
                db.refresh(img)
                imported += 1

        result = {
            "status": "success",
            "message": "Images imported successfully",
            "imported": imported,
            "updated": updated,
            "total": len(files)
        }

        if job:
            job.meta['result'] = result
            job.save_meta()

        logger.info(f"📊 Import completed: {imported} inserted, {updated} updated")
        return result

    except Exception as e:
        logger.error(f"❌ Import job failed: {str(e)}")
        logger.error(traceback.format_exc())
        error_result = {"status": "failed", "error": str(e), "imported": 0, "updated": 0, "total": 0}
        if job:
            job.meta['error'] = str(e)
            job.save_meta()
        return error_result

    finally:
        if db:
            db.close()
            logger.info("🔌 Database session closed")
