"""
Video upload and processing routes.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import aiofiles
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, Video, Clip
from app.routes.auth import get_current_user
from app.config import settings
from app.video_processor import VideoAnalyzer, VideoClipper
from app.content_generator import CaptionGenerator, HashtagGenerator

router = APIRouter(prefix="/api/videos", tags=["Videos"])


class VideoResponse(BaseModel):
    id: int
    filename: str
    duration: Optional[float]
    file_size: Optional[int]
    status: str
    processing_progress: int
    title: Optional[str]
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoProcessRequest(BaseModel):
    min_clip_duration: int = 15
    max_clip_duration: int = 60
    max_clips: int = 5
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []


class ClipResponse(BaseModel):
    id: int
    video_id: int
    filename: str
    start_time: float
    end_time: float
    duration: float
    score: Optional[float]
    caption: Optional[str]
    hashtags: List[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Initialize processors
video_analyzer = VideoAnalyzer()
video_clipper = VideoClipper()
caption_generator = CaptionGenerator()
hashtag_generator = HashtagGenerator()


async def process_video_task(video_id: int, request: VideoProcessRequest, db_url: str):
    """Background task to process video."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Get video
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            
            if not video:
                return
            
            # Update status
            video.status = "processing"
            video.title = request.title or video.filename
            video.description = request.description
            video.tags = request.tags
            await db.commit()
            
            # Analyze video
            def update_progress(progress, status):
                video.processing_progress = progress
            
            candidates = video_analyzer.analyze_video(
                video.original_path,
                min_clip_duration=request.min_clip_duration,
                max_clip_duration=request.max_clip_duration,
                max_clips=request.max_clips,
                progress_callback=update_progress
            )
            
            # Extract clips
            for i, candidate in enumerate(candidates):
                clip_result = video_clipper.extract_clip(
                    video.original_path,
                    candidate.start_time,
                    candidate.end_time
                )
                
                if clip_result.success:
                    # Generate caption and hashtags
                    caption = caption_generator.generate_caption(
                        title=video.title or "",
                        description=video.description or "",
                        tags=video.tags or []
                    )
                    
                    hashtags = hashtag_generator.generate_hashtags(
                        title=video.title or "",
                        description=video.description or "",
                        tags=video.tags or []
                    )
                    
                    # Create clip record
                    clip = Clip(
                        video_id=video.id,
                        filename=os.path.basename(clip_result.clip_path),
                        path=clip_result.clip_path,
                        start_time=candidate.start_time,
                        end_time=candidate.end_time,
                        duration=candidate.duration,
                        score=candidate.overall_score,
                        caption=caption,
                        hashtags=hashtags,
                        audio_peak_score=candidate.audio_score,
                        scene_change_score=candidate.scene_score,
                        motion_score=candidate.motion_score
                    )
                    db.add(clip)
            
            # Update video status
            video.status = "completed"
            video.processing_progress = 100
            await db.commit()
            
        except Exception as e:
            video.status = "failed"
            await db.commit()
            raise e


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a video file."""
    # Validate file type
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = settings.UPLOAD_DIR / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Check size limit
    if file_size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_VIDEO_SIZE_MB}MB"
        )
    
    # Get duration
    metadata = video_analyzer.get_video_metadata(str(file_path))
    
    # Create video record
    video = Video(
        user_id=current_user.id,
        filename=file.filename,
        original_path=str(file_path),
        duration=metadata.duration if metadata else None,
        file_size=file_size
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    return video


@router.post("/{video_id}/process", response_model=VideoResponse)
async def process_video(
    video_id: int,
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start processing a video to find and extract clips."""
    # Get video
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status == "processing":
        raise HTTPException(status_code=400, detail="Video is already being processed")
    
    # Start background processing
    video.status = "processing"
    video.processing_progress = 0
    await db.commit()
    
    background_tasks.add_task(
        process_video_task,
        video_id,
        request,
        settings.DATABASE_URL
    )
    
    await db.refresh(video)
    return video


@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all videos for the current user."""
    result = await db.execute(
        select(Video).where(Video.user_id == current_user.id).order_by(Video.created_at.desc())
    )
    videos = result.scalars().all()
    return videos


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific video."""
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video


@router.get("/{video_id}/clips", response_model=List[ClipResponse])
async def get_video_clips(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all clips for a video."""
    # Verify video ownership
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get clips
    result = await db.execute(
        select(Clip).where(Clip.video_id == video_id).order_by(Clip.score.desc())
    )
    clips = result.scalars().all()
    return clips


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a video and its clips."""
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete file
    if os.path.exists(video.original_path):
        os.remove(video.original_path)
    
    # Delete clips
    clips_result = await db.execute(select(Clip).where(Clip.video_id == video_id))
    for clip in clips_result.scalars().all():
        if os.path.exists(clip.path):
            os.remove(clip.path)
        await db.delete(clip)
    
    # Delete video record
    await db.delete(video)
    await db.commit()
    
    return {"message": "Video deleted successfully"}
