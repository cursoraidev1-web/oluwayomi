# API Routes
from .auth import router as auth_router
from .videos import router as videos_router
from .clips import router as clips_router
from .social import router as social_router

__all__ = ['auth_router', 'videos_router', 'clips_router', 'social_router']
