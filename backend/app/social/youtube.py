"""
YouTube API integration using OAuth 2.0.
Uses the free YouTube Data API for uploading Shorts.
"""
import httpx
import os
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging
import json

from .base import SocialMediaClient, PostResult, AuthResult
from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeClient(SocialMediaClient):
    """
    YouTube API client using OAuth 2.0.
    Uses the free YouTube Data API v3 for uploading videos/Shorts.
    
    Setup Instructions:
    1. Go to console.cloud.google.com
    2. Create a project
    3. Enable YouTube Data API v3
    4. Create OAuth 2.0 credentials
    5. Add callback URL to authorized redirects
    6. Get Client ID and Client Secret
    
    Note: YouTube API has a free quota of 10,000 units/day.
    Video upload costs 1600 units, so ~6 uploads/day for free.
    """
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    
    # OAuth 2.0 scopes needed
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.callback_url = settings.GOOGLE_CALLBACK_URL
    
    @property
    def platform_name(self) -> str:
        return "youtube"
    
    def get_auth_url(self, state: str) -> str:
        """
        Get Google OAuth 2.0 authorization URL.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> AuthResult:
        """
        Exchange authorization code for access token.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.callback_url
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.text}")
                    return AuthResult(success=False, error=response.text)
                
                data = response.json()
                
                # Get channel info
                channel_info = await self._get_channel_info(data["access_token"])
                
                return AuthResult(
                    success=True,
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600)),
                    user_id=channel_info.get("id"),
                    username=channel_info.get("title")
                )
                
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return AuthResult(success=False, error=str(e))
    
    async def refresh_access_token(self, refresh_token: str) -> AuthResult:
        """
        Refresh the access token.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code != 200:
                    return AuthResult(success=False, error=response.text)
                
                data = response.json()
                
                return AuthResult(
                    success=True,
                    access_token=data["access_token"],
                    refresh_token=refresh_token,  # Google doesn't return new refresh token
                    expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
                )
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResult(success=False, error=str(e))
    
    async def _get_channel_info(self, access_token: str) -> dict:
        """Get authenticated user's channel information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE}/channels",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={
                        "part": "snippet",
                        "mine": "true"
                    }
                )
                
                if response.status_code == 200:
                    items = response.json().get("items", [])
                    if items:
                        channel = items[0]
                        return {
                            "id": channel.get("id"),
                            "title": channel.get("snippet", {}).get("title")
                        }
                return {}
                
        except Exception:
            return {}
    
    async def verify_credentials(self, access_token: str) -> bool:
        """Verify that the access token is valid."""
        channel_info = await self._get_channel_info(access_token)
        return bool(channel_info.get("id"))
    
    async def post_video(
        self,
        access_token: str,
        video_path: str,
        caption: str,
        hashtags: list = None,
        **kwargs
    ) -> PostResult:
        """
        Upload a video to YouTube (as a Short if vertical).
        
        For YouTube Shorts:
        - Video must be vertical (9:16)
        - Duration must be <= 60 seconds
        - Add #Shorts to title/description
        """
        try:
            is_short = kwargs.get("is_short", True)
            
            # Prepare metadata
            title = kwargs.get("title", caption[:100])
            description = caption
            
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                description = f"{description}\n\n{hashtag_str}"
            
            # Add #Shorts tag for Shorts
            if is_short and "#shorts" not in description.lower():
                description = f"{description}\n\n#Shorts"
                if "#shorts" not in title.lower():
                    title = f"{title} #Shorts"
            
            # Video metadata
            metadata = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": hashtags or [],
                    "categoryId": "22"  # People & Blogs
                },
                "status": {
                    "privacyStatus": kwargs.get("privacy", "public"),
                    "selfDeclaredMadeForKids": False
                }
            }
            
            # Upload video
            file_size = os.path.getsize(video_path)
            
            async with httpx.AsyncClient(timeout=600) as client:
                # Initiate resumable upload
                init_response = await client.post(
                    f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Upload-Content-Length": str(file_size),
                        "X-Upload-Content-Type": "video/mp4"
                    },
                    json=metadata
                )
                
                if init_response.status_code != 200:
                    return PostResult(
                        success=False,
                        platform="youtube",
                        error=f"Upload init failed: {init_response.text}"
                    )
                
                upload_url = init_response.headers.get("Location")
                
                # Upload video content
                with open(video_path, 'rb') as f:
                    video_data = f.read()
                
                upload_response = await client.put(
                    upload_url,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(file_size)
                    },
                    content=video_data
                )
                
                if upload_response.status_code in [200, 201]:
                    data = upload_response.json()
                    video_id = data.get("id")
                    return PostResult(
                        success=True,
                        platform="youtube",
                        post_id=video_id,
                        post_url=f"https://youtube.com/shorts/{video_id}" if is_short else f"https://youtube.com/watch?v={video_id}"
                    )
                else:
                    return PostResult(
                        success=False,
                        platform="youtube",
                        error=upload_response.text
                    )
                    
        except Exception as e:
            logger.error(f"YouTube upload error: {e}")
            return PostResult(success=False, platform="youtube", error=str(e))
    
    async def get_upload_quota(self, access_token: str) -> dict:
        """
        Check remaining API quota.
        Note: This requires additional API scope.
        """
        # YouTube doesn't have a direct quota check API
        # You can monitor usage in Google Cloud Console
        return {
            "daily_limit": 10000,
            "cost_per_upload": 1600,
            "estimated_uploads_remaining": 6
        }
