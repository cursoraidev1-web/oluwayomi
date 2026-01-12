"""
Social media connection and posting routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import secrets

from app.database import get_db
from app.models import User, SocialAccount, Clip, Post
from app.routes.auth import get_current_user
from app.social import TwitterClient, YouTubeClient, TikTokClient

router = APIRouter(prefix="/api/social", tags=["Social Media"])

# Initialize clients
twitter_client = TwitterClient()
youtube_client = YouTubeClient()
tiktok_client = TikTokClient()

# Store OAuth state temporarily (use Redis in production)
oauth_states = {}


class SocialAccountResponse(BaseModel):
    id: int
    platform: str
    username: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PostRequest(BaseModel):
    clip_id: int
    platforms: List[str]
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class PostResponse(BaseModel):
    id: int
    clip_id: int
    platform: str
    status: str
    post_url: Optional[str] = None
    scheduled_at: Optional[datetime]
    posted_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# OAuth Authorization URLs

@router.get("/connect/twitter")
async def connect_twitter(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get Twitter OAuth URL."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": current_user.id,
        "platform": "twitter"
    }
    
    auth_url = twitter_client.get_auth_url(state)
    return {"auth_url": auth_url}


@router.get("/connect/youtube")
async def connect_youtube(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get YouTube OAuth URL."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": current_user.id,
        "platform": "youtube"
    }
    
    auth_url = youtube_client.get_auth_url(state)
    return {"auth_url": auth_url}


@router.get("/connect/tiktok")
async def connect_tiktok(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get TikTok OAuth URL."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": current_user.id,
        "platform": "tiktok"
    }
    
    auth_url = tiktok_client.get_auth_url(state)
    return {"auth_url": auth_url}


# OAuth Callbacks

@router.get("/auth/twitter/callback")
async def twitter_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Twitter OAuth callback."""
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    state_data = oauth_states.pop(state)
    
    result = await twitter_client.exchange_code(code)
    
    if not result.success:
        return RedirectResponse(f"/settings?error={result.error}")
    
    # Save account
    account = SocialAccount(
        user_id=state_data["user_id"],
        platform="twitter",
        platform_user_id=result.user_id,
        username=result.username,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_expires_at=result.expires_at
    )
    db.add(account)
    await db.commit()
    
    return RedirectResponse("/settings?connected=twitter")


@router.get("/auth/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google/YouTube OAuth callback."""
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    state_data = oauth_states.pop(state)
    
    result = await youtube_client.exchange_code(code)
    
    if not result.success:
        return RedirectResponse(f"/settings?error={result.error}")
    
    # Save account
    account = SocialAccount(
        user_id=state_data["user_id"],
        platform="youtube",
        platform_user_id=result.user_id,
        username=result.username,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_expires_at=result.expires_at
    )
    db.add(account)
    await db.commit()
    
    return RedirectResponse("/settings?connected=youtube")


@router.get("/auth/tiktok/callback")
async def tiktok_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle TikTok OAuth callback."""
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    state_data = oauth_states.pop(state)
    
    result = await tiktok_client.exchange_code(code)
    
    if not result.success:
        return RedirectResponse(f"/settings?error={result.error}")
    
    # Save account
    account = SocialAccount(
        user_id=state_data["user_id"],
        platform="tiktok",
        platform_user_id=result.user_id,
        username=result.username,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_expires_at=result.expires_at
    )
    db.add(account)
    await db.commit()
    
    return RedirectResponse("/settings?connected=tiktok")


# Account Management

@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List connected social media accounts."""
    result = await db.execute(
        select(SocialAccount)
        .where(SocialAccount.user_id == current_user.id, SocialAccount.is_active == True)
    )
    accounts = result.scalars().all()
    return accounts


@router.delete("/accounts/{account_id}")
async def disconnect_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect a social media account."""
    result = await db.execute(
        select(SocialAccount)
        .where(SocialAccount.id == account_id, SocialAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.is_active = False
    await db.commit()
    
    return {"message": "Account disconnected"}


# Posting

@router.post("/post", response_model=List[PostResponse])
async def post_clip(
    request: PostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Post a clip to selected social media platforms."""
    # Get clip
    clip_result = await db.execute(
        select(Clip)
        .join(Clip.video)
        .where(Clip.id == request.clip_id)
    )
    clip = clip_result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Get user's social accounts
    accounts_result = await db.execute(
        select(SocialAccount)
        .where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.is_active == True,
            SocialAccount.platform.in_(request.platforms)
        )
    )
    accounts = {acc.platform: acc for acc in accounts_result.scalars().all()}
    
    posts = []
    caption = request.caption or clip.caption
    hashtags = request.hashtags or clip.hashtags
    
    for platform in request.platforms:
        account = accounts.get(platform)
        
        if not account:
            # Create failed post record
            post = Post(
                clip_id=clip.id,
                social_account_id=0,
                platform=platform,
                caption=caption,
                hashtags=hashtags,
                status="failed",
                error_message=f"No {platform} account connected"
            )
            db.add(post)
            posts.append(post)
            continue
        
        # Create post record
        post = Post(
            clip_id=clip.id,
            social_account_id=account.id,
            platform=platform,
            caption=caption,
            hashtags=hashtags,
            scheduled_at=request.scheduled_at,
            status="scheduled" if request.scheduled_at else "pending"
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        
        # Post immediately if not scheduled
        if not request.scheduled_at:
            result = await _post_to_platform(
                platform=platform,
                account=account,
                clip=clip,
                caption=caption,
                hashtags=hashtags
            )
            
            if result["success"]:
                post.status = "posted"
                post.platform_post_id = result.get("post_id")
                post.posted_at = datetime.utcnow()
            else:
                post.status = "failed"
                post.error_message = result.get("error")
            
            await db.commit()
            await db.refresh(post)
        
        posts.append(post)
    
    await db.commit()
    return posts


async def _post_to_platform(
    platform: str,
    account: SocialAccount,
    clip: Clip,
    caption: str,
    hashtags: List[str]
) -> dict:
    """Post to a specific platform."""
    clients = {
        "twitter": twitter_client,
        "youtube": youtube_client,
        "tiktok": tiktok_client
    }
    
    client = clients.get(platform)
    if not client:
        return {"success": False, "error": "Unknown platform"}
    
    # Check token expiration and refresh if needed
    if account.token_expires_at and account.token_expires_at < datetime.utcnow():
        refresh_result = await client.refresh_access_token(account.refresh_token)
        if refresh_result.success:
            account.access_token = refresh_result.access_token
            if refresh_result.refresh_token:
                account.refresh_token = refresh_result.refresh_token
            account.token_expires_at = refresh_result.expires_at
        else:
            return {"success": False, "error": "Token refresh failed"}
    
    # Post video
    result = await client.post_video(
        access_token=account.access_token,
        video_path=clip.path,
        caption=caption,
        hashtags=hashtags,
        is_short=True  # For YouTube
    )
    
    return {
        "success": result.success,
        "post_id": result.post_id,
        "post_url": result.post_url,
        "error": result.error
    }


@router.get("/posts", response_model=List[PostResponse])
async def list_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all posts."""
    result = await db.execute(
        select(Post)
        .join(SocialAccount)
        .where(SocialAccount.user_id == current_user.id)
        .order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    return posts
