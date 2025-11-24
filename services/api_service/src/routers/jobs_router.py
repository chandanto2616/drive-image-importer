# services/api_service/src/routers/jobs_router.py
from fastapi import APIRouter, HTTPException
from redis import Redis
from rq import Queue
from rq.job import Job
from shared.config import REDIS_URL
from typing import List, Dict, Any
import json

router = APIRouter()

# Connect to redis and create queue
redis_conn = Redis.from_url(REDIS_URL)
q = Queue("default", connection=redis_conn)

@router.get("/jobs")
def list_jobs():
    """List recent import jobs"""
    jobs = []
    
    # Get recent jobs from different states
    for job_id in q.job_ids:
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            jobs.append({
                "id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result if job.result else None,
                "meta": job.meta if job.meta else {}
            })
        except Exception as e:
            # Job might have been cleaned up
            continue
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return {"jobs": jobs[:20]}  # Return last 20 jobs

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Get status of a specific job"""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result if job.result else None,
            "meta": job.meta if job.meta else {},
            "progress": job.meta.get("progress", 0) if job.meta else 0
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@router.get("/jobs/{job_id}/result")
def get_job_result(job_id: str):
    """Get the result of a completed job"""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        if job.get_status() != "finished":
            raise HTTPException(status_code=400, detail="Job not finished yet")
        
        return {
            "id": job.id,
            "result": job.result,
            "meta": job.meta if job.meta else {}
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
