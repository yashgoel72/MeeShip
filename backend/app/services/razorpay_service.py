"""
Razorpay Service Module

Handles Razorpay payment operations including:
- Order creation
- Payment signature verification
- Webhook signature verification
- Credit allocation
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

import razorpay
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.models.webhook_log import WebhookLog
from app.schemas.payment import CREDIT_PACKS

logger = logging.getLogger(__name__)


class RazorpayError(Exception):
    """Base exception for Razorpay operations."""
    pass


class InvalidPackError(RazorpayError):
    """Raised when an invalid pack_id is provided."""
    pass


class SignatureVerificationError(RazorpayError):
    """Raised when signature verification fails."""
    pass


class OrderNotFoundError(RazorpayError):
    """Raised when an order is not found."""
    pass


class OrderAlreadyProcessedError(RazorpayError):
    """Raised when an order has already been processed."""
    pass


class OrderOwnershipError(RazorpayError):
    """Raised when a user attempts to operate on another user's order."""
    pass


class RazorpayService:
    """Service for handling Razorpay payment operations."""

    def __init__(self, db: AsyncSession):
        """Initialize Razorpay service with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
        self._client: Optional[razorpay.Client] = None

    @property
    def client(self) -> razorpay.Client:
        """Lazy initialization of Razorpay client."""
        if self._client is None:
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                raise RazorpayError("Razorpay credentials not configured")
            self._client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        return self._client

    async def create_order(
        self,
        user: User,
        pack_id: str
    ) -> Tuple[Order, dict]:
        """Create a Razorpay order for credit purchase.
        
        Args:
            user: The authenticated user
            pack_id: Credit pack identifier (starter, pro, enterprise)
            
        Returns:
            Tuple of (Order model, Razorpay order response dict)
            
        Raises:
            InvalidPackError: If pack_id is not valid
            RazorpayError: If Razorpay API call fails
        """
        # Validate pack_id
        if pack_id not in CREDIT_PACKS:
            raise InvalidPackError(f"Invalid pack_id: {pack_id}")

        pack = CREDIT_PACKS[pack_id]
        amount_paise = pack["price_paise"]
        credits_to_purchase = pack["credits"]

        # Generate a unique receipt ID (max 40 chars for Razorpay)
        # Use last 8 chars of user_id + timestamp
        user_short = str(user.id).replace("-", "")[-8:]
        receipt = f"r_{user_short}_{int(datetime.utcnow().timestamp())}"

        # Create order in Razorpay
        try:
            razorpay_order = self.client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "notes": {
                    "pack_id": pack_id,
                    "credits": str(credits_to_purchase),
                    "user_id": str(user.id),
                    "user_email": user.email,
                }
            })
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            raise RazorpayError(f"Failed to create Razorpay order: {e}")

        # Create local order record
        order = Order(
            user_id=user.id,
            razorpay_order_id=razorpay_order["id"],
            amount_paise=amount_paise,
            credits_purchased=credits_to_purchase,
            pack_id=pack_id,
            status=OrderStatus.CREATED.value,
            receipt=receipt,
        )
        self.db.add(order)
        await self.db.flush()  # Get the order ID without committing

        logger.info(
            f"Created order {order.id} for user {user.id}, "
            f"pack={pack_id}, amount={amount_paise} paise"
        )

        return order, razorpay_order

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """Verify payment signature using HMAC-SHA256.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Signature from Razorpay
            
        Returns:
            True if signature is valid
        """
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            key=settings.RAZORPAY_KEY_SECRET.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

    def verify_webhook_signature(
        self,
        body: bytes,
        signature: str
    ) -> bool:
        """Verify webhook signature using HMAC-SHA256.
        
        Args:
            body: Raw request body bytes
            signature: X-Razorpay-Signature header value
            
        Returns:
            True if signature is valid
        """
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.warning("Webhook secret not configured, skipping verification")
            return True  # Allow in development
            
        expected_signature = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

    async def process_payment_verification(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        user_id: UUID,
    ) -> Tuple[Order, int]:
        """Process and verify payment, allocate credits.
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: HMAC signature from Razorpay
            
        Returns:
            Tuple of (updated Order, new credit balance)
            
        Raises:
            OrderNotFoundError: If order doesn't exist
            OrderAlreadyProcessedError: If order was already processed
            SignatureVerificationError: If signature is invalid
        """
        # Find the order
        result = await self.db.execute(
            select(Order).where(Order.razorpay_order_id == razorpay_order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise OrderNotFoundError(f"Order not found: {razorpay_order_id}")

        # Ensure the authenticated user owns this order
        if order.user_id != user_id:
            raise OrderOwnershipError("Order does not belong to the current user")

        # Check if already processed
        if order.status == OrderStatus.PAID.value:
            raise OrderAlreadyProcessedError(
                f"Order already processed: {razorpay_order_id}"
            )

        # Verify signature
        if not self.verify_payment_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        ):
            order.status = OrderStatus.FAILED.value
            await self.db.flush()
            raise SignatureVerificationError("Payment signature verification failed")

        # Update order
        order.razorpay_payment_id = razorpay_payment_id
        order.status = OrderStatus.PAID

        # Get user and add credits
        result = await self.db.execute(
            select(User).where(User.id == order.user_id)
        )
        user = result.scalar_one()
        
        user.credits += order.credits_purchased
        new_balance = user.credits

        # Set credit expiration based on pack validity
        if order.pack_id and order.pack_id in CREDIT_PACKS:
            validity_days = CREDIT_PACKS[order.pack_id].get("validity_days", 30)
            from datetime import timedelta
            new_expiry = datetime.utcnow() + timedelta(days=validity_days)
            # Extend expiry if user already has credits with later expiry
            if user.credits_expires_at is None or new_expiry > user.credits_expires_at:
                user.credits_expires_at = new_expiry

        await self.db.flush()

        logger.info(
            f"Payment verified for order {order.id}, "
            f"added {order.credits_purchased} credits to user {user.id}, "
            f"new balance: {new_balance}"
        )

        return order, new_balance

    async def process_webhook_event(
        self,
        event_id: str,
        event_type: str,
        payload: dict
    ) -> bool:
        """Process a webhook event with idempotency.
        
        Args:
            event_id: Unique event identifier
            event_type: Event type (e.g., payment.captured)
            payload: Event payload
            
        Returns:
            True if event was processed, False if already processed
        """
        # Check if already processed (idempotency)
        result = await self.db.execute(
            select(WebhookLog).where(WebhookLog.event_id == event_id)
        )
        existing_log = result.scalar_one_or_none()
        
        if existing_log:
            logger.info(f"Webhook event {event_id} already processed, skipping")
            return False

        # Create webhook log entry
        webhook_log = WebhookLog(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            processed=False,
        )
        self.db.add(webhook_log)
        await self.db.flush()

        # Process based on event type
        try:
            if event_type == "payment.captured":
                await self._handle_payment_captured(payload)
            elif event_type == "payment.failed":
                await self._handle_payment_failed(payload)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")

            # Mark as processed
            webhook_log.processed = True
            webhook_log.processed_at = datetime.utcnow()
            await self.db.flush()

            return True

        except Exception as e:
            logger.error(f"Error processing webhook {event_id}: {e}")
            # Log stays with processed=False for debugging
            raise

    async def _handle_payment_captured(self, payload: dict) -> None:
        """Handle payment.captured webhook event.
        
        Args:
            payload: Webhook payload
        """
        payment_entity = payload.get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")
        razorpay_payment_id = payment_entity.get("id")

        if not razorpay_order_id:
            logger.warning("No order_id in payment.captured payload")
            return

        # Find the order with lock
        result = await self.db.execute(
            select(Order)
            .where(Order.razorpay_order_id == razorpay_order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()

        if not order:
            logger.warning(f"Order not found for webhook: {razorpay_order_id}")
            return

        # Check if already paid (idempotency at order level)
        if order.status == OrderStatus.PAID.value:
            logger.info(f"Order {order.id} already paid, skipping credit allocation")
            return

        # Update order
        order.razorpay_payment_id = razorpay_payment_id
        order.status = OrderStatus.PAID.value

        # Get user and add credits
        result = await self.db.execute(
            select(User).where(User.id == order.user_id).with_for_update()
        )
        user = result.scalar_one()
        
        user.credits += order.credits_purchased

        # Set credit expiration based on pack validity
        if order.pack_id and order.pack_id in CREDIT_PACKS:
            validity_days = CREDIT_PACKS[order.pack_id].get("validity_days", 30)
            from datetime import timedelta
            new_expiry = datetime.utcnow() + timedelta(days=validity_days)
            if user.credits_expires_at is None or new_expiry > user.credits_expires_at:
                user.credits_expires_at = new_expiry

        logger.info(
            f"Webhook: Added {order.credits_purchased} credits to user {user.id} "
            f"for order {order.id}"
        )

    async def _handle_payment_failed(self, payload: dict) -> None:
        """Handle payment.failed webhook event.
        
        Args:
            payload: Webhook payload
        """
        payment_entity = payload.get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")

        if not razorpay_order_id:
            logger.warning("No order_id in payment.failed payload")
            return

        result = await self.db.execute(
            select(Order)
            .where(Order.razorpay_order_id == razorpay_order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()

        if order and order.status not in [OrderStatus.PAID.value, OrderStatus.FAILED.value]:
            order.status = OrderStatus.FAILED.value
            logger.info(f"Marked order {order.id} as failed via webhook")

    async def get_user_credit_balance(self, user_id: UUID) -> int:
        """Get current credit balance for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Current credit balance
        """
        result = await self.db.execute(
            select(User.credits).where(User.id == user_id)
        )
        return result.scalar_one_or_none() or 0

    async def get_user_orders(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[list, int]:
        """Get paginated order history for a user.
        
        Args:
            user_id: User UUID
            limit: Max orders to return
            offset: Pagination offset
            
        Returns:
            Tuple of (list of orders, total count)
        """
        # Get total count
        count_result = await self.db.execute(
            select(Order).where(Order.user_id == user_id)
        )
        total = len(count_result.scalars().all())

        # Get paginated orders
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        orders = result.scalars().all()

        return list(orders), total