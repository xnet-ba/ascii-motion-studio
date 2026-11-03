import shutil
from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/system/info")
async def system_info():
    total, used, free = shutil.disk_usage(str(settings.DATA_DIR))
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "limits": {
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            "max_video_duration_seconds": settings.MAX_VIDEO_DURATION_SECONDS,
            "max_ascii_width": settings.MAX_ASCII_WIDTH,
            "max_frames": settings.MAX_FRAMES,
            "concurrent_jobs": settings.CONCURRENT_JOBS,
        },
        "storage": {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
        },
    }
