"""
Authentication Router Module

Provides authentication endpoints for Kinde-authenticated users:
- GET /api/auth/me - Get current user profile
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.user import UserResponse
from app.middlewares.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Requires Kinde authentication via JWT token.
    
    Args:
        current_user: Current authenticated user from Kinde JWT
        db: Database session
        
    Returns:
        UserResponse with user details
    """
    subscription_tier: Optional[str] = None
    is_upgraded = False

    res = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    subscription = res.scalars().first()
    if subscription is not None:
        subscription_tier = subscription.tier
        is_upgraded = subscription.tier in {"pro", "premium"}

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        subscription_tier=subscription_tier,
        is_upgraded=is_upgraded,
    )
