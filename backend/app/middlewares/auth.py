"""
Authentication Middleware Module

Provides FastAPI dependencies for:
- JWT token verification
- Current user extraction
- Email verification requirements
- Subscription verification
"""

import logging
import os
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription

# Load .env file explicitly
load_dotenv()

logger = logging.getLogger(__name__)

# Security scheme for Bearer token authentication
security = HTTPBearer(auto_error=False)

# Dev mode bypass - set DEV_BYPASS_AUTH=true in .env for local testing
DEV_BYPASS_AUTH = os.environ.get("DEV_BYPASS_AUTH", "").lower() == "true"
logger.info(f"DEV_BYPASS_AUTH = {DEV_BYPASS_AUTH}")


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        User object for the authenticated user
        
    Raises:
        HTTPException: If token is missing, invalid, or user not found
    """
    # DEV MODE: Bypass auth and return/create a test user
    if DEV_BYPASS_AUTH:
        logger.warning("DEV_BYPASS_AUTH enabled - using test user")
        # Get or create test user
        result = await db.execute(
            select(User).where(User.email == "test@local.dev")
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="test@local.dev",
                full_name="Test User",
                email_verified=True,
                credits=1000,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created test user: {user.id}")
        return user
    
    if credentials is None:
        logger.warning(f"Missing authentication token from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Verify Kinde JWT (generated in kinde_auth.py callback)
    try:
        import jwt
        from app.config import Settings
        settings = Settings()
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
    except Exception as e:
        logger.warning(f"Invalid or expired token from {request.client.host}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user identifier from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query user from database
    try:
        user_uuid = UUID(user_id)
        result = await db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
    except ValueError:
        # Fallback to email-based lookup for legacy tokens
        result = await db.execute(
            select(User).where(User.email == user_id)
        )
        user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning(f"User not found for token: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional dependency to get current user if authenticated.
    Does not raise error if no token provided.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials (optional)
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    # In dev mode, always return the test user even without a token
    if DEV_BYPASS_AUTH:
        return await get_current_user(request, credentials, db)

    if credentials is None:
        return None
    
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


async def require_verified_email(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that requires the user's email to be verified.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if email is verified
        
    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.email_verified:
        logger.warning(f"Unverified user attempted restricted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )
    return current_user


async def require_active_subscription(
    current_user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that requires the user to have an active subscription
    or remaining trial uploads.
    
    Args:
        current_user: Current authenticated user with verified email
        db: Database session
        
    Returns:
        User object if subscription is valid
        
    Raises:
        HTTPException: If no valid subscription found
    """
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription is None:
        logger.warning(f"No subscription found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription required. Please subscribe to continue.",
        )
    
    # Check if trial has uploads remaining
    if subscription.tier == "trial" and subscription.trial_uploads_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Trial uploads exhausted. Please upgrade to continue.",
        )
    
    return current_user


async def get_user_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[Subscription]:
    """
    Get the current user's subscription.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Subscription object if exists, None otherwise
    """
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    return result.scalar_one_or_none()


async def require_meesho_linked(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that ensures the user has a valid, active Meesho session.
    
    Makes a lightweight API call to Meesho to verify the session cookie
    is still alive. Raises 403 with error codes:
    - MEESHO_NOT_LINKED: user hasn't linked their Meesho account
    - MEESHO_SESSION_EXPIRED: session cookie has expired
    """
    from app.services.meesho_service import MeeshoService
    
    meesho_service = MeeshoService(db)
    is_valid, error_msg, error_code = await meesho_service.ping_meesho_session(current_user)
    
    if not is_valid:
        logger.warning(f"Meesho session check failed for user {current_user.id}: {error_code} — {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": error_code,
                "message": error_msg,
            },
        )
    return current_user


async def require_meesho_or_platform(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Flexible Meesho dependency: allows generation with either user's own
    Meesho credentials OR the platform's shared credentials (for free-credit users).

    Logic:
    1. If user has linked Meesho → validate their session as normal.
    2. If user has NOT linked Meesho but has credits > 0 → allow through
       and tag request.state.use_platform_creds = True so the endpoint
       uses the platform's shared Meesho credentials for shipping cost calls.
    3. Otherwise → 403.
    """
    from app.services.meesho_service import MeeshoService

    meesho_service = MeeshoService(db)

    # Path A: User has their own Meesho linked — validate their session
    if meesho_service.is_linked(current_user):
        is_valid, error_msg, error_code = await meesho_service.ping_meesho_session(current_user)
        if is_valid:
            request.state.use_platform_creds = False
            return current_user
        # Session expired — tell frontend
        logger.warning(f"Meesho session expired for user {current_user.id}: {error_code}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": error_code, "message": error_msg},
        )

    # Path B: No Meesho linked — allow platform creds ONLY for free-credit users
    # who have never purchased (credits_expires_at is None means only free credits).
    # Users who have bought credits must link their own Meesho account.
    has_only_free_credits = (
        current_user.credits is not None
        and current_user.credits > 0
        and current_user.credits_expires_at is None
    )
    if has_only_free_credits:
        logger.info(
            f"User {current_user.id} has {current_user.credits} free credits (never purchased) — "
            "allowing with platform credentials"
        )
        request.state.use_platform_creds = True
        return current_user

    # Path C: No Meesho linked, and either no credits or has purchased credits — block
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "MEESHO_NOT_LINKED",
            "message": "Please link your Meesho account to continue.",
        },
    )


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request, considering proxies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address string
    """
    # Check for forwarded headers (reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"
