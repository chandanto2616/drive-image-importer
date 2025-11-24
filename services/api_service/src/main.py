from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from redis import Redis
from shared.models import Base
from shared.database import engine
from shared.config import REDIS_URL

# Create DB tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Import System - API (MVP)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}

# Readiness endpoint
@app.get("/ready")
def readiness():
    checks = {"database": False, "redis": False}

    # Database check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # Redis check
    try:
        redis_conn = Redis.from_url(REDIS_URL)
        redis_conn.ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all(checks.values()) else "not ready", "checks": checks},
    )

# Include API routers
from .routers import import_router, images_router, jobs_router
app.include_router(import_router)
app.include_router(images_router)
app.include_router(jobs_router)
