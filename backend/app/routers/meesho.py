"""
Meesho Account Linking Router

Endpoints for linking/unlinking Meesho accounts and calculating shipping costs.
Supports both manual credential entry and Playwright browser automation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.middlewares.auth import get_current_user
from app.services.meesho_service import MeeshoService
from app.services.meesho_playwright import MeeshoPlaywrightService, SessionStatus
from app.services.category_service import get_categories
from app.schemas.meesho import (
    LinkMeeshoRequest,
    LinkMeeshoResponse,
    UnlinkMeeshoResponse,
    MeeshoLinkStatus,
    SessionValidationResponse,
    ShippingCostRequest,
    ShippingCostResponse,
    ShippingCostError,
    PlaywrightSessionResponse,
    PlaywrightSessionStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meesho", tags=["meesho"])


@router.get("/categories")
async def list_categories():
    """
    Return all Meesho product sub-sub-categories with breadcrumb paths.

    No auth required — the taxonomy is public/static data.
    Response is a flat list of {id, name, breadcrumb} sorted alphabetically.
    """
    return get_categories()


@router.get("/status", response_model=MeeshoLinkStatus)
async def get_meesho_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current Meesho account linking status.
    
    Returns whether user has linked their Meesho account.
    """
    service = MeeshoService(db)
    
    return MeeshoLinkStatus(
        linked=service.is_linked(current_user),
        supplier_id=current_user.meesho_supplier_id,
        linked_at=current_user.meesho_linked_at
    )


@router.get("/validate-session", response_model=SessionValidationResponse)
async def validate_meesho_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate that the Meesho session is still active.
    
    Makes a lightweight API call to Meesho to verify the session token hasn't expired.
    Use this to proactively check session validity before operations.
    
    Returns:
        - valid: True if session is active
        - valid: False with error_code if session expired or not linked
    """
    service = MeeshoService(db)
    
    # Check if linked first
    if not service.is_linked(current_user):
        return SessionValidationResponse(
            valid=False,
            error_code="NOT_LINKED",
            message="Meesho account not linked. Please link your account."
        )
    
    # Validate session with Meesho API
    is_valid, error_message = await service.validate_session(current_user)
    
    if is_valid:
        return SessionValidationResponse(
            valid=True,
            message="Session is active"
        )
    else:
        # Determine error code based on message
        error_code = "SESSION_EXPIRED"
        if "unauthorized" in (error_message or "").lower():
            error_code = "SESSION_EXPIRED"
        elif "bot detection" in (error_message or "").lower():
            error_code = "BOT_DETECTED"
        
        return SessionValidationResponse(
            valid=False,
            error_code=error_code,
            message=error_message or "Your Meesho session has expired. Please re-link your account."
        )


@router.post("/link", response_model=LinkMeeshoResponse)
async def link_meesho_account(
    request: LinkMeeshoRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Link a Meesho account to the current user.
    
    The user must provide credentials obtained from their Meesho supplier dashboard:
    - supplier_id: Found in the dashboard URL or request headers
    - identifier: Found in request headers  
    - connect_sid: The connect.sid cookie from DevTools
    - browser_id: (Optional) The browser_id cookie
    
    The credentials are validated with Meesho's API before being stored (encrypted).
    """
    service = MeeshoService(db)
    
    # Check if already linked
    if service.is_linked(current_user):
        logger.info(f"User {current_user.id} re-linking Meesho account")
    
    # Attempt to link
    success, message = await service.link_account(
        user=current_user,
        supplier_id=request.supplier_id,
        identifier=request.identifier,
        connect_sid=request.connect_sid,
        browser_id=request.browser_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return LinkMeeshoResponse(
        success=True,
        message=message,
        supplier_id=request.supplier_id
    )


@router.post("/unlink", response_model=UnlinkMeeshoResponse)
async def unlink_meesho_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unlink the Meesho account from the current user.
    
    Removes all stored Meesho credentials.
    """
    service = MeeshoService(db)
    
    if not service.is_linked(current_user):
        return UnlinkMeeshoResponse(
            success=True,
            message="No Meesho account was linked"
        )
    
    success, message = await service.unlink_account(current_user)
    
    return UnlinkMeeshoResponse(
        success=success,
        message=message
    )


@router.post("/shipping-cost", response_model=ShippingCostResponse | ShippingCostError)
async def calculate_shipping_cost(
    request: ShippingCostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate shipping cost for a product.
    
    Uses the linked Meesho account to query Meesho's pricing API.
    Returns shipping charges, transfer price, commission, etc.
    
    Requires a linked Meesho account. If session expired, user will need to re-link.
    """
    service = MeeshoService(db)
    
    # Check if linked
    if not service.is_linked(current_user):
        return ShippingCostError(
            success=False,
            error="Meesho account not linked. Please link your account first.",
            error_code="NOT_LINKED"
        )
    
    # Get shipping cost
    result = await service.get_shipping_cost(
        user=current_user,
        price=request.price,
        sscat_id=request.sscat_id
    )
    
    if not result.success:
        return ShippingCostError(
            success=False,
            error=result.error or "Unknown error",
            error_code=result.error_code
        )
    
    return ShippingCostResponse(
        success=True,
        price=result.price,
        shipping_charges=result.shipping_charges,
        transfer_price=result.transfer_price,
        commission_fees=result.commission_fees,
        gst=result.gst,
        total_price=result.total_price,
        duplicate_pid=result.duplicate_pid
    )


# ============================================================================
# Playwright Browser Automation Endpoints
# ============================================================================

@router.post("/playwright/start", response_model=PlaywrightSessionResponse)
async def start_playwright_session(
    current_user: User = Depends(get_current_user),
):
    """
    Start a Playwright browser session for Meesho login.
    
    This opens a browser window where the user can log into their Meesho account.
    Credentials including HttpOnly cookies are captured automatically.
    
    Returns a session_id to poll for status.
    """
    try:
        session_id = await MeeshoPlaywrightService.create_session(str(current_user.id))
        
        return PlaywrightSessionResponse(
            session_id=session_id,
            status="pending",
            message="Browser window opening. Please log into your Meesho account."
        )
    except Exception as e:
        logger.error(f"Failed to start Playwright session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start browser session: {str(e)}"
        )


@router.get("/playwright/status/{session_id}", response_model=PlaywrightSessionStatus)
async def get_playwright_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a Playwright session.
    
    Poll this endpoint to check if login is complete.
    When status is "completed", the credentials are automatically saved.
    """
    session = MeeshoPlaywrightService.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    # Security: verify session belongs to current user
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not belong to current user"
        )
    
    result = PlaywrightSessionStatus(
        session_id=session.session_id,
        status=session.status.value,
        error=session.error
    )
    
    # If completed, save credentials to user
    if session.status == SessionStatus.COMPLETED and session.credentials:
        service = MeeshoService(db)
        success, message = await service.link_account(
            user=current_user,
            supplier_id=session.credentials.supplier_id,
            identifier=session.credentials.identifier,
            connect_sid=session.credentials.connect_sid,
            browser_id=session.credentials.browser_id
        )
        
        if success:
            result.linked = True
            result.supplier_id = session.credentials.supplier_id
            result.message = "Meesho account linked successfully!"
        else:
            result.error = message
    
    return result


@router.post("/playwright/cancel/{session_id}")
async def cancel_playwright_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel an active Playwright session."""
    session = MeeshoPlaywrightService.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not belong to current user"
        )
    
    await MeeshoPlaywrightService.cancel_session(session_id)
    
    return {"success": True, "message": "Session cancelled"}
