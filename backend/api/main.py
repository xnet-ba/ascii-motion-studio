import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import settings
from storage.db import init_db
from api.routes import upload, image, video, export, jobs, projects, health, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Professional ASCII Image, Video and Animation Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL, "https://go.kolektiv.pro", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(image.router, prefix="/api/v1", tags=["Image"])
app.include_router(video.router, prefix="/api/v1", tags=["Video"])
app.include_router(export.router, prefix="/api/v1", tags=["Export"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])

# Serve static exports
exports_dir = settings.DATA_DIR / "exports"
exports_dir.mkdir(parents=True, exist_ok=True)
app.mount("/exports", StaticFiles(directory=str(exports_dir)), name="exports")


@app.get("/")
async def root():
    return {"message": settings.APP_NAME, "version": "0.1.0"}
