"""
Payment Router Module

Provides payment endpoints:
- POST /api/payments/create-order - Create a Razorpay order
- POST /api/payments/verify - Verify payment and allocate credits
- POST /api/payments/webhook - Handle Razorpay webhooks
- GET /api/payments/balance - Get current credit balance
- GET /api/payments/orders - Get order history
- GET /api/payments/packs - Get available credit packs
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middlewares.auth import get_current_user
from app.models.user import User
from app.schemas.payment import (
    CREDIT_PACKS,
    CreateOrderRequest,
    CreateOrderResponse,
    CreditBalanceResponse,
    CreditPackInfo,
    CreditPacksResponse,
    OrderHistoryResponse,
    OrderSummary,
    PrefillInfo,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.services.razorpay_service import (
    InvalidPackError,
    OrderAlreadyProcessedError,
    OrderNotFoundError,
    OrderOwnershipError,
    RazorpayError,
    RazorpayService,
    SignatureVerificationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Razorpay order for credit purchase.
    
    Args:
        request: Contains pack_id (starter, pro, enterprise)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        CreateOrderResponse with order details for Razorpay checkout
        
    Raises:
        HTTPException 400: Invalid pack_id
        HTTPException 500: Razorpay API error
    """
    razorpay_service = RazorpayService(db)
    
    try:
        order, razorpay_order = await razorpay_service.create_order(
            user=current_user,
            pack_id=request.pack_id
        )
        await db.commit()
        
        pack = CREDIT_PACKS[request.pack_id]
        
        return CreateOrderResponse(
            order_id=razorpay_order["id"],
            amount=razorpay_order["amount"],
            currency=razorpay_order["currency"],
            key_id=settings.RAZORPAY_KEY_ID,
            prefill=PrefillInfo(
                email=current_user.email,
                name=current_user.full_name
            ),
            notes={
                "pack_id": request.pack_id,
                "credits": str(pack["credits"]),
                "user_id": str(current_user.id),
            }
        )
        
    except InvalidPackError as e:
        logger.warning(f"Invalid pack requested: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PACK", "message": str(e)}
        )
    except RazorpayError as e:
        logger.error(f"Razorpay error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "RAZORPAY_ERROR", "message": str(e)}
        )


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify payment signature and allocate credits.
    
    Args:
        request: Razorpay order_id, payment_id, and signature
        current_user: Authenticated user
        db: Database session
        
    Returns:
        VerifyPaymentResponse with success status and new balance
        
    Raises:
        HTTPException 400: Signature verification failed
        HTTPException 404: Order not found
        HTTPException 409: Order already processed
    """
    razorpay_service = RazorpayService(db)
    
    try:
        order, new_balance = await razorpay_service.process_payment_verification(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
            user_id=current_user.id,
        )
        await db.commit()
        
        # Refresh user to get updated expires_at
        await db.refresh(current_user)
        
        logger.info(
            f"Payment verified for user {current_user.id}, "
            f"credits added: {order.credits_purchased}, new balance: {new_balance}"
        )
        
        return VerifyPaymentResponse(
            success=True,
            message="Payment verified successfully",
            credits_added=order.credits_purchased,
            new_balance=new_balance,
            expires_at=current_user.credits_expires_at,
            order_id=order.id
        )
        
    except OrderNotFoundError as e:
        logger.warning(f"Order not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": str(e)}
        )
    except OrderAlreadyProcessedError as e:
        logger.warning(f"Order already processed: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ORDER_ALREADY_PROCESSED", "message": str(e)}
        )
    except SignatureVerificationError as e:
        logger.warning(f"Signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SIGNATURE_INVALID", "message": str(e)}
        )
    except OrderOwnershipError as e:
        logger.warning(f"Order ownership validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Order not found"}
        )
    except Exception as e:
        import traceback
        logger.error(
            f"Unexpected error in verify_payment for user {current_user.id}, "
            f"order {request.razorpay_order_id}: {type(e).__name__}: {e}\n"
            f"{traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Razorpay webhook events.
    
    No authentication required - uses webhook signature verification.
    
    Args:
        request: Raw HTTP request
        db: Database session
        
    Returns:
        200 OK on success
        
    Raises:
        HTTPException 400: Invalid webhook signature
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    razorpay_service = RazorpayService(db)
    
    # Verify webhook signature
    if not razorpay_service.verify_webhook_signature(body, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    try:
        # Parse payload
        import json
        payload = json.loads(body)
        
        event_type = payload.get("event", "")
        # Prefer Razorpay's webhook event id if present; otherwise build a stable composite.
        # NOTE: Do NOT use payment id alone, as multiple event types can share the same payment id.
        event_id = payload.get("id") or payload.get("event_id") or ""
        if not event_id:
            payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "")
            created_at = payload.get("created_at", "")
            event_id = f"{event_type}:{payment_id}:{created_at}"
        
        # Process the webhook
        processed = await razorpay_service.process_webhook_event(
            event_id=event_id,
            event_type=event_type,
            payload=payload
        )
        
        await db.commit()
        
        if processed:
            logger.info(f"Webhook processed: {event_type} ({event_id})")
        else:
            logger.info(f"Webhook skipped (duplicate): {event_type} ({event_id})")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        await db.rollback()
        # Return 200 to prevent Razorpay retries for application errors
        # The webhook will be logged with processed=False for debugging
        return {"status": "error", "message": str(e)}


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's credit balance.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        CreditBalanceResponse with current credits
    """
    razorpay_service = RazorpayService(db)
    credits = await razorpay_service.get_user_credit_balance(current_user.id)
    
    return CreditBalanceResponse(
        credits=credits,
        user_id=current_user.id,
        expires_at=current_user.credits_expires_at
    )


@router.get("/orders", response_model=OrderHistoryResponse)
async def get_orders(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's order history.
    
    Args:
        limit: Max orders to return (default 10, max 50)
        offset: Pagination offset
        current_user: Authenticated user
        db: Database session
        
    Returns:
        OrderHistoryResponse with paginated orders
    """
    # Enforce limits
    limit = min(max(1, limit), 50)
    offset = max(0, offset)
    
    razorpay_service = RazorpayService(db)
    orders, total = await razorpay_service.get_user_orders(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    # Map to response format
    order_summaries: List[OrderSummary] = []
    for order in orders:
        # Get pack name from credits_purchased
        pack_name = "Unknown Pack"
        for pack_id, pack_info in CREDIT_PACKS.items():
            if pack_info["credits"] == order.credits_purchased:
                pack_name = pack_info["name"]
                break
        
        order_summaries.append(OrderSummary(
            id=order.id,
            pack_name=pack_name,
            credits=order.credits_purchased,
            amount_inr=order.amount_paise // 100,
            status=order.status.value if hasattr(order.status, 'value') else str(order.status),
            created_at=order.created_at
        ))
    
    return OrderHistoryResponse(
        orders=order_summaries,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/packs", response_model=CreditPacksResponse)
async def get_credit_packs():
    """
    Get available credit packs.
    
    No authentication required.
    
    Returns:
        CreditPacksResponse with all available packs
    """
    packs = [
        CreditPackInfo(
            id=pack_id,
            name=pack_info["name"],
            credits=pack_info["credits"],
            price_inr=pack_info["price_inr"],
            price_paise=pack_info["price_paise"],
            per_image_cost=pack_info["per_image_cost"],
            validity_days=pack_info["validity_days"]
        )
        for pack_id, pack_info in CREDIT_PACKS.items()
    ]
    
    return CreditPacksResponse(packs=packs)