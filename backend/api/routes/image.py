from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Tuple
from core.security import verify_token
from core.config import settings
from storage import db
from workers.job import enqueue_job
from engines.ascii.renderer import PALETTES

router = APIRouter()


class ImageConvertRequest(BaseModel):
    input_path: str
    project_id: Optional[int] = None
    width: int = Field(default=120, ge=10, le=240)
    height: Optional[int] = Field(default=None, ge=10, le=200)
    mode: str = "grayscale"
    palette: str = "standard"
    custom_chars: Optional[str] = None
    background: str = "black"
    background_color: Optional[Tuple[int, int, int]] = None
    brightness: float = Field(default=1.0, ge=0.1, le=3.0)
    contrast: float = Field(default=1.0, ge=0.1, le=3.0)
    gamma: float = Field(default=1.0, ge=0.1, le=3.0)
    saturation: float = Field(default=1.0, ge=0.0, le=3.0)
    sharpen: float = Field(default=0.0, ge=0.0, le=2.0)
    edge: bool = False
    denoise: bool = False
    quantize: int = Field(default=0, ge=0, le=64)
    contrast_adapt: bool = False
    output_format: str = "png"

    class Config:
        protected_namespaces = ()


@router.post("/image/convert")
async def convert_image(payload: ImageConvertRequest, token: str = Depends(verify_token)):
    input_path = Path(payload.input_path)
    if not input_path.exists():
        raise HTTPException(400, "Input file not found")
    if payload.width > settings.MAX_ASCII_WIDTH:
        raise HTTPException(400, f"Width exceeds max {settings.MAX_ASCII_WIDTH}")

    job_id = db.create_job(payload.project_id, f"image_{payload.output_format}", str(input_path))
    enqueue_job(job_id, "image", {
        "input_path": str(input_path),
        "options": payload.model_dump(),
    })
    return {"job_id": job_id, "status": "pending"}
