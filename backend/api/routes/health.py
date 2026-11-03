from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
