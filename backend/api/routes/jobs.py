from fastapi import APIRouter, HTTPException, Depends
from core.security import verify_token
from storage import db

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: int, token: str = Depends(verify_token)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/jobs/{job_id}/progress")
async def get_job_progress(job_id: int, token: str = Depends(verify_token)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "output_path": job["output_path"],
        "result": job["result"],
    }


@router.get("/jobs")
async def list_jobs(limit: int = 100, token: str = Depends(verify_token)):
    return {"jobs": db.list_jobs(limit)}
