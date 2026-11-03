from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from core.security import verify_token
from core.config import settings
from storage.files import save_upload
import magic

router = APIRouter()

ALLOWED_IMAGE = {"image/png", "image/jpeg", "image/webp", "image/bmp", "image/gif", "image/svg+xml"}
ALLOWED_VIDEO = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo"}
ALLOWED_TYPES = ALLOWED_IMAGE | ALLOWED_VIDEO | {"application/octet-stream"}


def _type_from_magic(data: bytes, declared: str) -> str:
    try:
        detected = magic.from_buffer(data, mime=True)
    except Exception:
        detected = declared
    if b"<svg" in data[:1024].lower():
        return "image/svg+xml"
    if detected in ("application/octet-stream", "text/plain", "text/xml"):
        return declared
    return detected


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), token: str = Depends(verify_token)):
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB)")

    detected = _type_from_magic(data, file.content_type or "")
    if detected not in ALLOWED_TYPES:
        raise HTTPException(415, f"Unsupported file type: {detected}")

    source_type = "image" if detected in ALLOWED_IMAGE else "video"
    saved = save_upload(data, file.filename or "upload")
    return {
        "success": True,
        "path": str(saved),
        "filename": file.filename,
        "type": source_type,
        "mime": detected,
        "size_bytes": len(data),
    }
