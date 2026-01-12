"""
Base class for social media clients.
All implementations use free developer APIs.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PostResult:
    """Result of posting to social media."""
    success: bool
    platform: str
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AuthResult:
    """Result of OAuth authentication."""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    error: Optional[str] = None


class SocialMediaClient(ABC):
    """
    Abstract base class for social media clients.
    All implementations use official free APIs with OAuth.
    """
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name."""
        pass
    
    @abstractmethod
    def get_auth_url(self, state: str) -> str:
        """
        Get the OAuth authorization URL.
        
        Args:
            state: Random state for security
            
        Returns:
            Authorization URL for the user to visit
        """
        pass
    
    @abstractmethod
    async def exchange_code(self, code: str) -> AuthResult:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            AuthResult with tokens
        """
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> AuthResult:
        """
        Refresh the access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            AuthResult with new tokens
        """
        pass
    
    @abstractmethod
    async def post_video(
        self,
        access_token: str,
        video_path: str,
        caption: str,
        hashtags: list = None,
        **kwargs
    ) -> PostResult:
        """
        Post a video to the platform.
        
        Args:
            access_token: User's access token
            video_path: Path to video file
            caption: Post caption
            hashtags: List of hashtags
            
        Returns:
            PostResult with post details
        """
        pass
    
    @abstractmethod
    async def verify_credentials(self, access_token: str) -> bool:
        """
        Verify that the access token is valid.
        
        Args:
            access_token: User's access token
            
        Returns:
            True if credentials are valid
        """
        pass
