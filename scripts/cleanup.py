#!/usr/bin/env python3
"""Remove old temporary and export files."""
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/ascii-motion-studio/backend")
from core.config import settings
from storage.db import delete_old_jobs

MAX_AGE_HOURS = 48
MAX_JOB_AGE_DAYS = 7


def remove_old(path: Path, max_age_hours: int) -> int:
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    if not path.exists():
        return 0
    for item in path.iterdir():
        try:
            mtime = item.stat().st_mtime
            if mtime < cutoff:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed += 1
        except Exception as e:
            print(f"Failed to remove {item}: {e}")
    return removed


def main() -> None:
    print(f"[{datetime.utcnow().isoformat()}] Starting cleanup")
    temp_removed = remove_old(settings.TEMP_DIR / "jobs", MAX_AGE_HOURS)
    export_removed = remove_old(settings.DATA_DIR / "exports", MAX_AGE_HOURS * 7)
    cutoff = (datetime.utcnow() - timedelta(days=MAX_JOB_AGE_DAYS)).isoformat()
    jobs_removed = delete_old_jobs(cutoff)
    print(f"Removed {temp_removed} temp dirs, {export_removed} old exports and {jobs_removed} stale jobs")


if __name__ == "__main__":
    main()
