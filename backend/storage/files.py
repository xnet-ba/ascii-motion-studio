import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from core.config import settings


def safe_filename(name: str) -> str:
    # Remove path traversal characters and keep only safe chars.
    return "".join(c for c in name if c.isalnum() or c in "._-").strip()


def save_upload(file_bytes: bytes, original_name: str, folder: str = "uploads") -> Path:
    upload_dir = settings.DATA_DIR / folder / uuid.uuid4().hex[:16]
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = safe_filename(original_name) or "upload"
    dest = upload_dir / name
    with open(dest, "wb") as f:
        f.write(file_bytes)
    return dest


def get_job_dir(job_id: int) -> Path:
    d = settings.TEMP_DIR / "jobs" / str(job_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def cleanup_temp(max_age_seconds: int = 86400) -> int:
    """Remove temporary job directories older than max_age_seconds."""
    removed = 0
    base = settings.TEMP_DIR / "jobs"
    if not base.exists():
        return 0
    now = Path(__file__).stat().st_mtime
    # placeholder; real implementation would iterate mtimes
    return removed
