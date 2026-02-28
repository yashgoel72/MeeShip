"""
Platform Credential Service

Manages the platform's shared Meesho credentials used for free-credit users
who haven't linked their own Meesho account. Stores credentials on a dedicated
platform dummy user row and auto-refreshes via Playwright when the session expires.
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.services.meesho_service import (
    MeeshoAPIClient,
    MeeshoCredentials,
    MeeshoService,
)

logger = logging.getLogger(__name__)

# Module-level lock to prevent concurrent Playwright refresh attempts
_refresh_lock = asyncio.Lock()


async def get_platform_user(db: AsyncSession) -> Optional[User]:
    """
    Fetch the dedicated platform dummy user from the database.
    Identified by the well-known email in settings.PLATFORM_USER_EMAIL.
    """
    result = await db.execute(
        select(User).where(User.email == settings.PLATFORM_USER_EMAIL)
    )
    return result.scalar_one_or_none()


async def get_platform_credentials(db: AsyncSession) -> Optional[MeeshoCredentials]:
    """
    Return a MeeshoCredentials object built from the platform user's stored fields.
    Returns None if the platform user doesn't exist or has no linked credentials.
    """
    platform_user = await get_platform_user(db)
    if platform_user is None:
        logger.warning("Platform user not found in database")
        return None

    meesho_service = MeeshoService(db)
    if not meesho_service.is_linked(platform_user):
        logger.info("Platform user exists but has no Meesho credentials linked")
        return None

    return meesho_service._get_credentials(platform_user)


async def _refresh_via_playwright(db: AsyncSession, platform_user: User) -> bool:
    """
    Re-login to Meesho using the platform email+password via Playwright subprocess,
    then store the fresh credentials on the platform user row.

    Returns True on success, False on failure.
    """
    email = settings.PLATFORM_MEESHO_EMAIL
    password = settings.PLATFORM_MEESHO_PASSWORD

    if not email or not password:
        logger.error(
            "Cannot refresh platform Meesho session: "
            "PLATFORM_MEESHO_EMAIL / PLATFORM_MEESHO_PASSWORD not set"
        )
        return False

    logger.info("Starting Playwright refresh for platform Meesho credentials...")

    try:
        from app.services.meesho_playwright import MeeshoPlaywrightService

        # Start a programmatic login session
        session_id = await MeeshoPlaywrightService.create_session(
            user_id=str(platform_user.id),
            email=email,
            password=password,
        )

        # Poll until completion (timeout ~60s)
        for _ in range(120):  # 120 × 0.5s = 60s
            status = MeeshoPlaywrightService.get_session_status(session_id)
            if status["status"] == "completed":
                creds = MeeshoPlaywrightService.get_session(session_id).credentials
                if creds is None:
                    logger.error("Playwright session completed but credentials are None")
                    return False

                # Store fresh credentials on the platform user via MeeshoService
                meesho_service = MeeshoService(db)
                success, msg = await meesho_service.link_account(
                    user=platform_user,
                    supplier_id=creds.supplier_id,
                    identifier=creds.identifier,
                    connect_sid=creds.connect_sid,
                    browser_id=creds.browser_id,
                )
                if success:
                    logger.info(
                        "Platform Meesho credentials refreshed successfully "
                        f"(supplier_id={creds.supplier_id})"
                    )
                else:
                    logger.error(f"Failed to link refreshed credentials: {msg}")
                return success

            if status["status"] in ("failed", "expired", "cancelled"):
                logger.error(
                    f"Playwright refresh failed with status={status['status']}, "
                    f"error={status.get('error')}"
                )
                return False

            await asyncio.sleep(0.5)

        logger.error("Playwright refresh timed out after 60s")
        return False

    except Exception as e:
        logger.exception(f"Playwright refresh error: {e}")
        return False


async def ensure_valid_session(db: AsyncSession) -> Optional[MeeshoCredentials]:
    """
    Return valid platform MeeshoCredentials, refreshing via Playwright if expired.

    Uses an asyncio.Lock so that concurrent requests don't spawn parallel
    Playwright browsers — they wait for the first refresh to complete and
    then reuse the updated credentials.

    Returns None if credentials are unavailable or refresh fails.
    """
    platform_user = await get_platform_user(db)
    if platform_user is None:
        logger.warning("Platform user not found — cannot provide platform credentials")
        return None

    meesho_service = MeeshoService(db)

    # Fast path: credentials exist and session is alive
    if meesho_service.is_linked(platform_user):
        credentials = meesho_service._get_credentials(platform_user)
        if credentials:
            async with MeeshoAPIClient(credentials) as client:
                is_valid, error = await client.ping_session()
            if is_valid:
                return credentials
            logger.warning(f"Platform Meesho session expired: {error}")

    # Slow path: refresh under lock
    async with _refresh_lock:
        # Double-check after acquiring lock (another request may have refreshed)
        await db.refresh(platform_user)
        if meesho_service.is_linked(platform_user):
            credentials = meesho_service._get_credentials(platform_user)
            if credentials:
                async with MeeshoAPIClient(credentials) as client:
                    is_valid, _ = await client.ping_session()
                if is_valid:
                    return credentials

        # Actually refresh
        success = await _refresh_via_playwright(db, platform_user)
        if not success:
            return None

        # Re-read freshly stored credentials
        await db.refresh(platform_user)
        return meesho_service._get_credentials(platform_user)
