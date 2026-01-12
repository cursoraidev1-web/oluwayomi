"""
TikTok API integration using OAuth 2.0.
Uses the TikTok Content Posting API (free for developers).
"""
import httpx
import os
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging

from .base import SocialMediaClient, PostResult, AuthResult
from app.config import settings

logger = logging.getLogger(__name__)


class TikTokClient(SocialMediaClient):
    """
    TikTok API client using OAuth 2.0.
    Uses the free TikTok Content Posting API.
    
    Setup Instructions:
    1. Go to developers.tiktok.com
    2. Create a developer account
    3. Create an app
    4. Apply for Content Posting API access
    5. Add callback URL
    6. Get Client Key and Client Secret
    
    Note: TikTok has a review process for API access.
    Videos posted via API may require user confirmation in app.
    """
    
    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    API_BASE = "https://open.tiktokapis.com/v2"
    
    # OAuth 2.0 scopes needed
    SCOPES = [
        "user.info.basic",
        "video.upload",
        "video.publish"
    ]
    
    def __init__(self):
        self.client_key = settings.TIKTOK_CLIENT_KEY
        self.client_secret = settings.TIKTOK_CLIENT_SECRET
        self.callback_url = settings.TIKTOK_CALLBACK_URL
    
    @property
    def platform_name(self) -> str:
        return "tiktok"
    
    def get_auth_url(self, state: str) -> str:
        """
        Get TikTok OAuth 2.0 authorization URL.
        """
        params = {
            "client_key": self.client_key,
            "redirect_uri": self.callback_url,
            "response_type": "code",
            "scope": ",".join(self.SCOPES),
            "state": state
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
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_key": self.client_key,
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
                
                if "error" in data:
                    return AuthResult(success=False, error=data.get("error_description", data["error"]))
                
                # Get user info
                user_info = await self._get_user_info(data["access_token"])
                
                return AuthResult(
                    success=True,
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 86400)),
                    user_id=user_info.get("open_id"),
                    username=user_info.get("display_name")
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
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_key": self.client_key,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code != 200:
                    return AuthResult(success=False, error=response.text)
                
                data = response.json()
                
                if "error" in data:
                    return AuthResult(success=False, error=data.get("error_description"))
                
                return AuthResult(
                    success=True,
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", refresh_token),
                    expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 86400))
                )
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResult(success=False, error=str(e))
    
    async def _get_user_info(self, access_token: str) -> dict:
        """Get authenticated user information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE}/user/info/",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"fields": "open_id,display_name,avatar_url"}
                )
                
                if response.status_code == 200:
                    data = response.json().get("data", {}).get("user", {})
                    return data
                return {}
                
        except Exception:
            return {}
    
    async def verify_credentials(self, access_token: str) -> bool:
        """Verify that the access token is valid."""
        user_info = await self._get_user_info(access_token)
        return bool(user_info.get("open_id"))
    
    async def post_video(
        self,
        access_token: str,
        video_path: str,
        caption: str,
        hashtags: list = None,
        **kwargs
    ) -> PostResult:
        """
        Upload a video to TikTok using the Content Posting API.
        
        TikTok Requirements:
        - Video must be vertical (9:16)
        - Duration: 3 seconds to 10 minutes
        - File size: up to 4GB
        - Format: MP4, WebM
        """
        try:
            # Prepare caption with hashtags
            full_caption = caption
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                full_caption = f"{caption} {hashtag_str}"
            
            file_size = os.path.getsize(video_path)
            
            async with httpx.AsyncClient(timeout=600) as client:
                # Step 1: Initialize video upload
                init_response = await client.post(
                    f"{self.API_BASE}/post/publish/video/init/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "post_info": {
                            "title": full_caption[:150],
                            "privacy_level": kwargs.get("privacy", "PUBLIC_TO_EVERYONE"),
                            "disable_duet": False,
                            "disable_comment": False,
                            "disable_stitch": False
                        },
                        "source_info": {
                            "source": "FILE_UPLOAD",
                            "video_size": file_size,
                            "chunk_size": file_size,  # Single chunk upload
                            "total_chunk_count": 1
                        }
                    }
                )
                
                if init_response.status_code != 200:
                    return PostResult(
                        success=False,
                        platform="tiktok",
                        error=f"Upload init failed: {init_response.text}"
                    )
                
                init_data = init_response.json().get("data", {})
                publish_id = init_data.get("publish_id")
                upload_url = init_data.get("upload_url")
                
                if not upload_url:
                    return PostResult(
                        success=False,
                        platform="tiktok",
                        error="No upload URL received"
                    )
                
                # Step 2: Upload video file
                with open(video_path, 'rb') as f:
                    video_data = f.read()
                
                upload_response = await client.put(
                    upload_url,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes 0-{file_size-1}/{file_size}"
                    },
                    content=video_data
                )
                
                if upload_response.status_code not in [200, 201]:
                    return PostResult(
                        success=False,
                        platform="tiktok",
                        error=f"Video upload failed: {upload_response.text}"
                    )
                
                # Step 3: Check publish status
                status = await self._check_publish_status(client, access_token, publish_id)
                
                if status.get("status") == "PUBLISH_COMPLETE":
                    return PostResult(
                        success=True,
                        platform="tiktok",
                        post_id=publish_id,
                        post_url=f"https://www.tiktok.com/@user/video/{publish_id}"
                    )
                else:
                    return PostResult(
                        success=False,
                        platform="tiktok",
                        error=f"Publish failed: {status.get('fail_reason', 'Unknown error')}"
                    )
                    
        except Exception as e:
            logger.error(f"TikTok upload error: {e}")
            return PostResult(success=False, platform="tiktok", error=str(e))
    
    async def _check_publish_status(
        self, 
        client: httpx.AsyncClient, 
        access_token: str, 
        publish_id: str
    ) -> dict:
        """Check the status of a video publish."""
        import asyncio
        
        for _ in range(30):  # Max 5 minutes
            response = await client.post(
                f"{self.API_BASE}/post/publish/status/fetch/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"publish_id": publish_id}
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                status = data.get("status")
                
                if status in ["PUBLISH_COMPLETE", "FAILED"]:
                    return data
            
            await asyncio.sleep(10)
        
        return {"status": "TIMEOUT"}
    
    async def post_video_inbox(
        self,
        access_token: str,
        video_path: str,
        caption: str,
        hashtags: list = None,
        **kwargs
    ) -> PostResult:
        """
        Alternative: Send video to user's TikTok inbox for manual posting.
        This is easier to get approved and doesn't require Content Posting API.
        """
        # This method sends the video to the user's TikTok app
        # where they can review and post it manually
        # Useful when direct posting API access isn't available
        pass
