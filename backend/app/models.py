"""
Database models for ClipForge.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    videos = relationship("Video", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user")


class SocialAccount(Base):
    """Connected social media accounts."""
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # twitter, youtube, tiktok
    platform_user_id = Column(String(255))
    username = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="social_accounts")


class Video(Base):
    """Uploaded video model."""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    duration = Column(Float)
    file_size = Column(Integer)
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    processing_progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata extracted from video
    title = Column(String(255))
    description = Column(Text)
    tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    clips = relationship("Clip", back_populates="video")


class Clip(Base):
    """Generated video clip model."""
    __tablename__ = "clips"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    score = Column(Float)  # Interest score (0-100)
    
    # Generated content
    caption = Column(Text)
    hashtags = Column(JSON, default=list)
    
    # Clip analysis data
    audio_peak_score = Column(Float)
    scene_change_score = Column(Float)
    motion_score = Column(Float)
    
    # Status
    status = Column(String(50), default="generated")  # generated, approved, posted, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="clips")
    posts = relationship("Post", back_populates="clip")


class Post(Base):
    """Social media post model."""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=False)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    
    # Post details
    platform = Column(String(50), nullable=False)
    platform_post_id = Column(String(255))
    caption = Column(Text)
    hashtags = Column(JSON, default=list)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)
    status = Column(String(50), default="pending")  # pending, scheduled, posted, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clip = relationship("Clip", back_populates="posts")
    social_account = relationship("SocialAccount")
