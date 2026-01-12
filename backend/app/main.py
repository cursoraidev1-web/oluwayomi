"""
ClipForge - Automated Video Clipping and Social Media Posting
Main FastAPI application.

No monthly subscriptions required - all tools are free and self-hosted:
- FFmpeg for video processing
- PySceneDetect for scene detection
- Librosa for audio analysis
- SQLite for database
- Official social media APIs (free tier)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.routes import auth_router, videos_router, clips_router, social_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ClipForge - Automated Video Clipping and Social Media Posting
    
    ## Features
    - 📹 Upload videos and automatically find the best moments
    - ✂️ Extract clips based on audio peaks, scene changes, and motion
    - 📝 Auto-generate engaging captions and hashtags
    - 🐦 Post to Twitter, YouTube Shorts, and TikTok
    - 📅 Schedule posts for optimal engagement
    
    ## No Monthly Fees
    All processing is done locally using free, open-source tools:
    - FFmpeg for video processing
    - PySceneDetect for scene detection
    - Librosa for audio analysis
    - SQLite for database
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for clips
app.mount("/clips", StaticFiles(directory=str(settings.CLIPS_DIR)), name="clips")

# Include routers
app.include_router(auth_router)
app.include_router(videos_router)
app.include_router(clips_router)
app.include_router(social_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
