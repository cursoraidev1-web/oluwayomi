"""
Twitter/X API integration using OAuth 2.0.
Uses the free Twitter API v2 (Basic tier is free for posting).
"""
import httpx
import base64
import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging

from .base import SocialMediaClient, PostResult, AuthResult
from app.config import settings

logger = logging.getLogger(__name__)


class TwitterClient(SocialMediaClient):
    """
    Twitter/X API client using OAuth 2.0 PKCE.
    Uses the free Basic tier API for posting videos.
    
    Setup Instructions:
    1. Go to developer.twitter.com
    2. Create a project and app
    3. Enable OAuth 2.0 with PKCE
    4. Add callback URL
    5. Get Client ID and Client Secret
    """
    
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    API_BASE = "https://api.twitter.com/2"
    UPLOAD_URL = "https://upload.twitter.com/1.1"
    
    # OAuth 2.0 scopes needed
    SCOPES = [
        "tweet.read",
        "tweet.write",
        "users.read",
        "offline.access"
    ]
    
    def __init__(self):
        self.client_id = settings.TWITTER_CLIENT_ID
        self.client_secret = settings.TWITTER_CLIENT_SECRET
        self.callback_url = settings.TWITTER_CALLBACK_URL
        
        # PKCE code verifier and challenge
        self._code_verifier = None
    
    @property
    def platform_name(self) -> str:
        return "twitter"
    
    def _generate_pkce(self) -> tuple:
        """Generate PKCE code verifier and challenge."""
        # Generate random code verifier
        verifier = secrets.token_urlsafe(32)
        
        # Create code challenge (S256)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return verifier, challenge
    
    def get_auth_url(self, state: str) -> str:
        """
        Get Twitter OAuth 2.0 authorization URL with PKCE.
        """
        self._code_verifier, code_challenge = self._generate_pkce()
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code(self, code: str, code_verifier: str = None) -> AuthResult:
        """
        Exchange authorization code for access token.
        """
        try:
            verifier = code_verifier or self._code_verifier
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.callback_url,
                        "code_verifier": verifier,
                        "client_id": self.client_id
                    },
                    auth=(self.client_id, self.client_secret) if self.client_secret else None
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.text}")
                    return AuthResult(success=False, error=response.text)
                
                data = response.json()
                
                # Get user info
                user_info = await self._get_user_info(data["access_token"])
                
                return AuthResult(
                    success=True,
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 7200)),
                    user_id=user_info.get("id"),
                    username=user_info.get("username")
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
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.client_id
                    }
                )
                
                if response.status_code != 200:
                    return AuthResult(success=False, error=response.text)
                
                data = response.json()
                
                return AuthResult(
                    success=True,
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", refresh_token),
                    expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 7200))
                )
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResult(success=False, error=str(e))
    
    async def _get_user_info(self, access_token: str) -> dict:
        """Get authenticated user information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE}/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json().get("data", {})
                return {}
                
        except Exception:
            return {}
    
    async def verify_credentials(self, access_token: str) -> bool:
        """Verify that the access token is valid."""
        user_info = await self._get_user_info(access_token)
        return bool(user_info.get("id"))
    
    async def post_video(
        self,
        access_token: str,
        video_path: str,
        caption: str,
        hashtags: list = None,
        **kwargs
    ) -> PostResult:
        """
        Post a video tweet.
        
        Note: Twitter API v2 video upload requires chunked upload.
        This implementation handles the full upload process.
        """
        try:
            # Step 1: Initialize upload
            media_id = await self._upload_video(access_token, video_path)
            
            if not media_id:
                return PostResult(
                    success=False,
                    platform="twitter",
                    error="Video upload failed"
                )
            
            # Step 2: Create tweet with media
            full_text = caption
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags[:5])  # Twitter limit
                if len(full_text) + len(hashtag_str) + 1 <= 280:
                    full_text = f"{full_text}\n\n{hashtag_str}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_BASE}/tweets",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": full_text[:280],
                        "media": {"media_ids": [media_id]}
                    }
                )
                
                if response.status_code in [200, 201]:
                    data = response.json().get("data", {})
                    return PostResult(
                        success=True,
                        platform="twitter",
                        post_id=data.get("id"),
                        post_url=f"https://twitter.com/i/status/{data.get('id')}"
                    )
                else:
                    return PostResult(
                        success=False,
                        platform="twitter",
                        error=response.text
                    )
                    
        except Exception as e:
            logger.error(f"Tweet posting error: {e}")
            return PostResult(success=False, platform="twitter", error=str(e))
    
    async def _upload_video(self, access_token: str, video_path: str) -> Optional[str]:
        """
        Upload video using chunked upload (Twitter v1.1 API).
        """
        import os
        
        try:
            file_size = os.path.getsize(video_path)
            
            async with httpx.AsyncClient(timeout=300) as client:
                # INIT
                init_response = await client.post(
                    f"{self.UPLOAD_URL}/media/upload.json",
                    headers={"Authorization": f"Bearer {access_token}"},
                    data={
                        "command": "INIT",
                        "media_type": "video/mp4",
                        "total_bytes": file_size,
                        "media_category": "tweet_video"
                    }
                )
                
                if init_response.status_code != 202:
                    logger.error(f"Upload INIT failed: {init_response.text}")
                    return None
                
                media_id = init_response.json()["media_id_string"]
                
                # APPEND (chunked)
                chunk_size = 5 * 1024 * 1024  # 5MB chunks
                segment_index = 0
                
                with open(video_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        
                        append_response = await client.post(
                            f"{self.UPLOAD_URL}/media/upload.json",
                            headers={"Authorization": f"Bearer {access_token}"},
                            data={
                                "command": "APPEND",
                                "media_id": media_id,
                                "segment_index": segment_index
                            },
                            files={"media": chunk}
                        )
                        
                        segment_index += 1
                
                # FINALIZE
                finalize_response = await client.post(
                    f"{self.UPLOAD_URL}/media/upload.json",
                    headers={"Authorization": f"Bearer {access_token}"},
                    data={
                        "command": "FINALIZE",
                        "media_id": media_id
                    }
                )
                
                if finalize_response.status_code not in [200, 201]:
                    logger.error(f"Upload FINALIZE failed: {finalize_response.text}")
                    return None
                
                # Check processing status
                result = finalize_response.json()
                if "processing_info" in result:
                    await self._wait_for_processing(client, access_token, media_id)
                
                return media_id
                
        except Exception as e:
            logger.error(f"Video upload error: {e}")
            return None
    
    async def _wait_for_processing(self, client, access_token: str, media_id: str):
        """Wait for video processing to complete."""
        import asyncio
        
        for _ in range(30):  # Max 5 minutes
            response = await client.get(
                f"{self.UPLOAD_URL}/media/upload.json",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "command": "STATUS",
                    "media_id": media_id
                }
            )
            
            if response.status_code == 200:
                info = response.json().get("processing_info", {})
                state = info.get("state")
                
                if state == "succeeded":
                    return
                elif state == "failed":
                    raise Exception("Video processing failed")
                
                wait_time = info.get("check_after_secs", 10)
                await asyncio.sleep(wait_time)
