"""
Configuration settings for ClipForge.
All settings use environment variables for security.
No paid services required - everything is self-hosted.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "ClipForge"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database (SQLite - free, no maintenance)
    DATABASE_URL: str = "sqlite+aiosqlite:///./clipforge.db"
    
    # File storage paths
    UPLOAD_DIR: Path = Path("./uploads")
    CLIPS_DIR: Path = Path("./clips")
    TEMP_DIR: Path = Path("./temp")
    
    # Video processing settings
    MAX_VIDEO_SIZE_MB: int = 500
    CLIP_MIN_DURATION: int = 15  # seconds
    CLIP_MAX_DURATION: int = 60  # seconds
    MAX_CLIPS_PER_VIDEO: int = 10
    
    # FFmpeg settings (free, open-source)
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    
    # Social Media OAuth (free developer APIs)
    # Twitter/X
    TWITTER_CLIENT_ID: Optional[str] = None
    TWITTER_CLIENT_SECRET: Optional[str] = None
    TWITTER_CALLBACK_URL: str = "http://localhost:8000/api/auth/twitter/callback"
    
    # YouTube (Google)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CALLBACK_URL: str = "http://localhost:8000/api/auth/google/callback"
    
    # TikTok
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None
    TIKTOK_CALLBACK_URL: str = "http://localhost:8000/api/auth/tiktok/callback"
    
    # Redis for background tasks (optional - can use in-memory)
    REDIS_URL: Optional[str] = None
    USE_CELERY: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Create directories if they don't exist
for dir_path in [settings.UPLOAD_DIR, settings.CLIPS_DIR, settings.TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
