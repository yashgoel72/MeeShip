"""
Payment Schemas Module

Pydantic models for Razorpay payment integration.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Credit Pack Configuration
CREDIT_PACKS = {
    "starter": {
        "name": "MeeShip Trial",
        "credits": 10,
        "price_inr": 99,
        "price_paise": 9900,
        "per_image_cost": 9.90,
        "validity_days": 7,
    },
    "pro": {
        "name": "MeeShip Pro",
        "credits": 75,
        "price_inr": 499,
        "price_paise": 49900,
        "per_image_cost": 6.65,
        "validity_days": 30,
    },
    "enterprise": {
        "name": "MeeShip Max",
        "credits": 250,
        "price_inr": 999,
        "price_paise": 99900,
        "per_image_cost": 4.00,
        "validity_days": 90,
    },
}


# Request Schemas
class CreateOrderRequest(BaseModel):
    """Request schema for creating a Razorpay order."""
    pack_id: str = Field(..., description="Credit pack ID: starter, pro, or enterprise")


class VerifyPaymentRequest(BaseModel):
    """Request schema for verifying payment signature."""
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID")
    razorpay_signature: str = Field(..., description="HMAC-SHA256 signature")


# Response Schemas
class PrefillInfo(BaseModel):
    """Prefill information for Razorpay checkout."""
    email: str
    name: Optional[str] = None


class CreateOrderResponse(BaseModel):
    """Response schema for order creation."""
    order_id: str = Field(..., description="Razorpay order ID")
    amount: int = Field(..., description="Amount in paise")
    currency: str = Field(default="INR", description="Currency code")
    key_id: str = Field(..., description="Razorpay key ID for frontend")
    prefill: PrefillInfo
    notes: Dict[str, str] = Field(default_factory=dict)


class VerifyPaymentResponse(BaseModel):
    """Response schema for payment verification."""
    success: bool
    message: str
    credits_added: int = 0
    new_balance: int = 0
    expires_at: Optional[datetime] = None
    order_id: Optional[UUID] = None


class CreditBalanceResponse(BaseModel):
    """Response schema for credit balance query."""
    credits: int
    user_id: UUID
    expires_at: Optional[datetime] = None


class OrderSummary(BaseModel):
    """Summary of a single order for history."""
    id: UUID
    pack_name: str
    credits: int
    amount_inr: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderHistoryResponse(BaseModel):
    """Response schema for order history."""
    orders: List[OrderSummary]
    total: int
    limit: int
    offset: int


# Error Response Schema
class PaymentErrorDetail(BaseModel):
    """Error detail for payment errors."""
    code: str
    message: str
    details: Optional[str] = None


class PaymentErrorResponse(BaseModel):
    """Error response schema for payment endpoints."""
    error: PaymentErrorDetail


# Webhook Schemas
class WebhookPayload(BaseModel):
    """Schema for Razorpay webhook payload."""
    event: str
    payload: Dict


# Credit Pack Info Schema
class CreditPackInfo(BaseModel):
    """Information about a credit pack."""
    id: str
    name: str
    credits: int
    price_inr: int
    price_paise: int
    per_image_cost: float
    validity_days: int


class CreditPacksResponse(BaseModel):
    """Response schema for listing credit packs."""
    packs: List[CreditPackInfo]