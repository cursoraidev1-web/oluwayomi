"""
Clip management routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from app.database import get_db
from app.models import User, Video, Clip
from app.routes.auth import get_current_user
from app.content_generator import CaptionGenerator, HashtagGenerator

router = APIRouter(prefix="/api/clips", tags=["Clips"])


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
    audio_peak_score: Optional[float]
    scene_change_score: Optional[float]
    motion_score: Optional[float]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClipUpdateRequest(BaseModel):
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: Optional[str] = None


class RegenerateContentRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    platform: str = "general"


caption_generator = CaptionGenerator()
hashtag_generator = HashtagGenerator()


@router.get("/", response_model=List[ClipResponse])
async def list_clips(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all clips for the current user."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Video.user_id == current_user.id)
        .order_by(Clip.created_at.desc())
    )
    clips = result.scalars().all()
    return clips


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific clip."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Clip.id == clip_id, Video.user_id == current_user.id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return clip


@router.get("/{clip_id}/download")
async def download_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a clip file."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Clip.id == clip_id, Video.user_id == current_user.id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if not os.path.exists(clip.path):
        raise HTTPException(status_code=404, detail="Clip file not found")
    
    return FileResponse(
        clip.path,
        media_type="video/mp4",
        filename=clip.filename
    )


@router.patch("/{clip_id}", response_model=ClipResponse)
async def update_clip(
    clip_id: int,
    update: ClipUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update clip caption, hashtags, or status."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Clip.id == clip_id, Video.user_id == current_user.id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if update.caption is not None:
        clip.caption = update.caption
    if update.hashtags is not None:
        clip.hashtags = update.hashtags
    if update.status is not None:
        if update.status not in ["generated", "approved", "posted", "failed"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        clip.status = update.status
    
    await db.commit()
    await db.refresh(clip)
    
    return clip


@router.post("/{clip_id}/regenerate-content", response_model=ClipResponse)
async def regenerate_content(
    clip_id: int,
    request: RegenerateContentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate caption and hashtags for a clip."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Clip.id == clip_id, Video.user_id == current_user.id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Regenerate caption
    clip.caption = caption_generator.generate_caption(
        title=request.title or "",
        description=request.description or "",
        tags=request.tags,
        platform=request.platform
    )
    
    # Regenerate hashtags
    clip.hashtags = hashtag_generator.generate_hashtags(
        title=request.title or "",
        description=request.description or "",
        tags=request.tags,
        platform=request.platform
    )
    
    await db.commit()
    await db.refresh(clip)
    
    return clip


@router.delete("/{clip_id}")
async def delete_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a clip."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Clip.id == clip_id, Video.user_id == current_user.id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Delete file
    if os.path.exists(clip.path):
        os.remove(clip.path)
    
    await db.delete(clip)
    await db.commit()
    
    return {"message": "Clip deleted successfully"}


@router.get("/{clip_id}/preview")
async def preview_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get clip preview data for the UI."""
    result = await db.execute(
        select(Clip)
        .join(Video)
        .where(Clip.id == clip_id, Video.user_id == current_user.id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Get video info
    video_result = await db.execute(select(Video).where(Video.id == clip.video_id))
    video = video_result.scalar_one()
    
    return {
        "clip": ClipResponse.model_validate(clip),
        "video_title": video.title or video.filename,
        "preview_url": f"/api/clips/{clip_id}/download",
        "formatted_hashtags": " ".join(f"#{tag}" for tag in clip.hashtags),
        "scores": {
            "overall": clip.score,
            "audio": clip.audio_peak_score,
            "scene": clip.scene_change_score,
            "motion": clip.motion_score
        }
    }
