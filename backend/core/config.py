import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ASCII Motion Studio"
    APP_ENV: str = "production"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8001
    APP_URL: str = "https://go.kolektiv.pro"

    SECRET_KEY: str = "change-me-please"
    API_TOKEN: str = "demo-token-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    APP_DIR: Path = Path("/opt/ascii-motion-studio")
    DATA_DIR: Path = Path("/var/lib/ascii-motion-studio")
    LOG_DIR: Path = Path("/var/log/ascii-motion-studio")
    TEMP_DIR: Path = Path("/var/tmp/ascii-motion-studio")

    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_VIDEO_DURATION_SECONDS: int = 20
    MAX_VIDEO_WIDTH: int = 1920
    MAX_VIDEO_HEIGHT: int = 1080
    MAX_ASCII_WIDTH: int = 240
    MAX_FRAMES: int = 300
    CONCURRENT_JOBS: int = 2

    DEFAULT_FPS: int = 15
    DEFAULT_ASCII_WIDTH: int = 120
    DEFAULT_VIDEO_DURATION_LIMIT: int = 20

    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    FFPROBE_PATH: str = "/usr/bin/ffprobe"
    IMAGEMAGICK_CONVERT_PATH: str = "/usr/bin/convert"
    IMAGEMAGICK_IDENTIFY_PATH: str = "/usr/bin/identify"

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
for d in (settings.DATA_DIR, settings.LOG_DIR, settings.TEMP_DIR,
          settings.DATA_DIR / "uploads", settings.DATA_DIR / "exports",
          settings.TEMP_DIR / "jobs"):
    d.mkdir(parents=True, exist_ok=True)
