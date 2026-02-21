"""
Meesho Account Linking Schemas

Pydantic models for Meesho API requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Request Schemas
# ============================================================================

class LinkMeeshoRequest(BaseModel):
    """Request to link Meesho account with credentials from DevTools."""
    supplier_id: str = Field(..., description="Supplier ID from Meesho (e.g., '248070')")
    identifier: str = Field(..., description="Identifier/tag from Meesho (e.g., 'jglfp')")
    connect_sid: str = Field(..., description="connect.sid cookie value from Meesho")
    browser_id: Optional[str] = Field(None, description="browser_id cookie (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "248070",
                "identifier": "jglfp",
                "connect_sid": "s%3Axxxxxx.yyyyy",
                "browser_id": "NnQgKyAyMzMgKy..."
            }
        }


class ShippingCostRequest(BaseModel):
    """Request to calculate shipping cost for an image."""
    image_url: str = Field(..., description="URL of the product image")
    price: int = Field(..., ge=1, description="Product price in INR")
    sscat_id: int = Field(default=12435, description="Sub-category ID (default: 12435)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/image.jpg",
                "price": 200,
                "sscat_id": 12435
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class MeeshoLinkStatus(BaseModel):
    """Status of Meesho account linking."""
    linked: bool = Field(..., description="Whether Meesho account is linked")
    supplier_id: Optional[str] = Field(None, description="Linked supplier ID")
    linked_at: Optional[datetime] = Field(None, description="When account was linked")
    session_valid: Optional[bool] = Field(None, description="Whether session is still valid (only set if checked)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "linked": True,
                "supplier_id": "248070",
                "linked_at": "2026-01-25T23:30:00Z",
                "session_valid": True
            }
        }


class SessionValidationResponse(BaseModel):
    """Response from session validation endpoint."""
    valid: bool = Field(..., description="Whether the session is still valid")
    error_code: Optional[str] = Field(None, description="Error code if invalid (SESSION_EXPIRED, NOT_LINKED)")
    message: Optional[str] = Field(None, description="Human-readable message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": False,
                "error_code": "SESSION_EXPIRED",
                "message": "Your Meesho session has expired. Please re-link your account."
            }
        }


class LinkMeeshoResponse(BaseModel):
    """Response after linking Meesho account."""
    success: bool
    message: str
    supplier_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Meesho account linked successfully",
                "supplier_id": "248070"
            }
        }


class UnlinkMeeshoResponse(BaseModel):
    """Response after unlinking Meesho account."""
    success: bool
    message: str


class ShippingCostResponse(BaseModel):
    """Response with shipping cost calculation."""
    success: bool
    price: int = Field(..., description="Input product price")
    shipping_charges: int = Field(..., description="Shipping cost in INR")
    transfer_price: float = Field(..., description="Amount seller receives")
    commission_fees: float = Field(default=0, description="Meesho commission")
    gst: float = Field(default=0, description="GST amount")
    total_price: int = Field(..., description="Total price including shipping")
    duplicate_pid: Optional[int] = Field(None, description="Duplicate product ID if found")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "price": 200,
                "shipping_charges": 73,
                "transfer_price": 186.59,
                "commission_fees": 0,
                "gst": 15.66,
                "total_price": 273,
                "duplicate_pid": None
            }
        }


class ShippingCostError(BaseModel):
    """Error response for shipping cost calculation."""
    success: bool = False
    error: str
    error_code: Optional[str] = None  # e.g., "SESSION_EXPIRED", "NOT_LINKED"
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Meesho session expired. Please re-link your account.",
                "error_code": "SESSION_EXPIRED"
            }
        }


# ============================================================================
# Playwright Session Schemas
# ============================================================================

class PlaywrightSessionResponse(BaseModel):
    """Response when starting a Playwright browser session."""
    session_id: str = Field(..., description="Unique session ID for polling")
    status: str = Field(..., description="Current session status")
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "message": "Browser window opening. Please log into your Meesho account."
            }
        }


class PlaywrightSessionStatus(BaseModel):
    """Status of a Playwright browser session."""
    session_id: str
    status: str = Field(..., description="pending|browser_open|logged_in|capturing|completed|failed|cancelled")
    error: Optional[str] = None
    linked: bool = False
    supplier_id: Optional[str] = None
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "linked": True,
                "supplier_id": "248070",
                "message": "Meesho account linked successfully!"
            }
        }
