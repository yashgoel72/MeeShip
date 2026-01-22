"""
Kinde Authentication Routes
Handles OAuth login, callback, and logout flows
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import secrets
from typing import Optional
from datetime import datetime, timedelta
import jwt

from app.config import Settings
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription


router = APIRouter(prefix="/api/auth/kinde", tags=["kinde-auth"])
settings = Settings()

# In-memory store for OAuth state (use Redis in production)
_oauth_states = {}


@router.get("/login")
async def kinde_login():
    """
    Redirect user to Kinde login page
    Generates OAuth state for CSRF protection
    """
    if not settings.KINDE_DOMAIN or not settings.KINDE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kinde configuration missing. Set KINDE_DOMAIN and KINDE_CLIENT_ID"
        )
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.utcnow()
    
    # Build Kinde authorization URL
    auth_url = (
        f"{settings.KINDE_DOMAIN}/oauth2/auth"
        f"?client_id={settings.KINDE_CLIENT_ID}"
        f"&redirect_uri={settings.KINDE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid profile email"
        f"&state={state}"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def kinde_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from Kinde
    Exchanges code for tokens and creates/updates user
    """
    # Check for OAuth errors
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kinde authentication failed: {error}"
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter"
        )
    
    # Verify state to prevent CSRF attacks
    if state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Clean up old states (older than 10 minutes)
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    _oauth_states.clear()  # Simple cleanup for now
    
    # Exchange authorization code for tokens
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{settings.KINDE_DOMAIN}/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.KINDE_CLIENT_ID,
                    "client_secret": settings.KINDE_CLIENT_SECRET,
                    "redirect_uri": settings.KINDE_REDIRECT_URI,
                    "code": code
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_response.raise_for_status()
            tokens = token_response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange code for tokens: {str(e)}"
        )
    
    # Decode ID token to get user info (without verification for simplicity)
    # In production, verify the token signature
    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No ID token received from Kinde"
        )
    
    try:
        # Decode without verification (Kinde tokens are already verified via HTTPS)
        user_info = jwt.decode(id_token, options={"verify_signature": False})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decode ID token: {str(e)}"
        )
    
    # Extract user details from token
    kinde_id = user_info.get("sub")
    email = user_info.get("email")
    full_name = user_info.get("given_name", "") + " " + user_info.get("family_name", "")
    full_name = full_name.strip() or email.split("@")[0]
    
    if not kinde_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required user information from Kinde"
        )
    
    # Check if user exists by kinde_id
    result = await db.execute(
        select(User).where(User.kinde_id == kinde_id)
    )
    user = result.scalar_one_or_none()
    
    # If not found by kinde_id, check by email (for account linking)
    if not user:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Update existing user with kinde_id
        if user:
            user.kinde_id = kinde_id
            user.email_verified = True  # Kinde verifies emails
            await db.commit()
    
    # Create new user if doesn't exist
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            kinde_id=kinde_id,
            email_verified=True,  # Kinde handles email verification
            hashed_password=None,  # No password for Kinde users
            credits=1,  # New users get 1 free credit
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Generate JWT access token for frontend
    access_token = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "kinde_id": kinde_id,
            "exp": datetime.utcnow() + timedelta(hours=1)
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )
    
    # Redirect to frontend with token
    # Frontend will store this token and use it for API calls
    frontend_url = settings.KINDE_LOGOUT_REDIRECT_URI or "http://localhost:3000"
    redirect_url = f"{frontend_url}?token={access_token}&kinde_token={tokens['access_token']}"
    
    return RedirectResponse(url=redirect_url)


@router.get("/logout")
async def kinde_logout():
    """
    Redirect user to Kinde logout endpoint
    """
    logout_url = (
        f"{settings.KINDE_DOMAIN}/logout"
        f"?redirect={settings.KINDE_LOGOUT_REDIRECT_URI}"
    )
    
    return RedirectResponse(url=logout_url)


@router.get("/user")
async def get_kinde_user_info(request: Request):
    """
    Get current user info (for debugging)
    Requires Authorization: Bearer <kinde_token> header
    """
    # This endpoint can be used to verify Kinde tokens during development
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    # Fetch user info from Kinde
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.KINDE_DOMAIN}/oauth2/v2/user_profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to fetch user info: {str(e)}"
        )
