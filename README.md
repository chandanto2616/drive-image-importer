# Drive Import Project

## Project Overview

**Drive Import** is a image import system that:

* Imports images from a public Google Drive folder.
* Uploads images to Cloudinary.
* Tracks images in a PostgreSQL database.
* Offers a frontend interface to submit folder IDs and monitor import jobs.

The system consists of three main components:

1. **API Service** – Receives requests and enqueues jobs.
2. **Worker Service** – Processes jobs, downloads, uploads, and updates the database.
3. **Frontend** – Interface to trigger and monitor imports.

---

## Live Application

**Frontend URL:** [https://foto-owl-frontend.onrender.com/](https://foto-owl-frontend.onrender.com/)

**GitHub Repository:** [https://github.com/Bhushan-04/Drive_import](https://github.com/Bhushan-04/Drive_import)

---

## Setup Instructions

###  Local Setup

#### Backend API Service

```bash
cd services/api_service
python -m venv .venv
source .venv/bin/activate   
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 10000
```

#### Worker Service

```bash
cd services/worker_service
python -m venv .venv
source .venv/bin/activate 
pip install -r requirements.txt
python -m src.worker
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

### Cloud Deployment (Render)

1. **PostgreSQL** – Create managed DB and note internal/external URL.
2. **Redis** – Create managed Redis and copy URL.
3. **API Service**

   * Environment: Python 3.12.3
   * Start Command: `uvicorn services.api_service.src.main:app --host 0.0.0.0 --port 10000`
   * Environment variables: `DATABASE_URL`, `REDIS_URL`, `SERVICE_ACCOUNT_JSON`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`,      `CLOUDINARY_API_SECRET`
4. **Worker Service**

   * Environment: Python 3.12.3
   * Start Command: `python -m services.worker_service.src.worker`
   * Environment variables: Same as API Service
5. **Frontend**

   * Deploy as **Static Site** (Render or Vercel)
   * Build Command: `npm install && npm run build`
   * Publish Directory: `frontend/dist`
   * Environment variable: `VITE_API_BASE`

---

## API Documentation

### Import Images

**POST** `https://image-import-api.onrender.com/import/google-drive`

**Request Body:**

```json
{
    "folder_url":"https://drive.google.com/drive/folders/1u8HCnZSPFzVQPTI4laGwdVqfKta16HsB"
}
```

**Response:**

```json
{
    "message": "Import started in background",
    "folder_id": "1u8HCnZSPFzVQPTI4laGwdVqfKta16HsB",
    "job_id": "eaabec63-0d93-431b-bd24-b4c48ea33c5f"
}
```

---

### Check Job Status

**GET** `https://image-import-api.onrender.com/jobs/ba67e4df-7217-4414-83e1-b22aea8b1e28`

**Response:**

```json
{
    "id": "ba67e4df-7217-4414-83e1-b22aea8b1e28",
    "status": "finished",
    "created_at": "2025-10-13T21:16:42.556867+00:00",
    "started_at": "2025-10-13T21:16:42.578612+00:00",
    "ended_at": "2025-10-13T21:17:00.097871+00:00",
    "result": {
        "status": "success",
        "message": "Images imported successfully",
        "imported": 3,
        "updated": 0,
        "total": 3
    },
    "meta": {
        "result": {
            "status": "success",
            "message": "Images imported successfully",
            "imported": 3,
            "updated": 0,
            "total": 3
        }
    },
    "progress": 0
}
```

---

### Get all images

**GET** `https://image-import-api.onrender.com/images`

**Response:**

```json
{
    "items": [
        {
            "id": 1,
            "name": "img1.jpg",
            "google_drive_id": "1h-wSkRBMeyKe9hsbrAZkhhcAt9EnO-F8",
            "size": 4164566,
            "mime_type": "image/jpeg",
            "storage_path": "img1.jpg",
            "url": "https://res.cloudinary.com/dlwg34kwj/image/upload/v1760378280/img1.jpg"
        },
        {
            "id": 2,
            "name": "img2.jpg",
            "google_drive_id": "1RLvzyC9UpTnprCmAgBuafCo9HO4licPi",
            "size": 3783979,
            "mime_type": "image/jpeg",
            "storage_path": "img2.jpg",
            "url": "https://res.cloudinary.com/dlwg34kwj/image/upload/v1760378297/img2.jpg"
        }
    ],
    "total": 2,
    "limit": 50,
    "offset": 0
}
```

---

## Architecture & Service Breakdown

* **API Service**: Receives requests, enqueues jobs in Redis.
* **Worker Service**: Downloads images, uploads to Cloudinary, writes to Postgres.
* **Frontend**: Provides a user interface to submit folder IDs and monitor jobs.

---

##Postman Collection 
[click here to see postman collection](https://viniciiii02-4518108.postman.co/workspace/viniciiii's-Workspace~60ce975b-8aaf-4e60-8c4d-ff08be66f374/collection/48743463-cba0d48f-5633-418a-8530-a816d74fb9a7?action=share&creator=48743463)

