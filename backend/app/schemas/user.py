from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    email_verified: bool = False
    credits: int = 0  # Total credits (paid + trial)
    credits_expires_at: Optional[datetime] = Field(default=None, alias="creditsExpiresAt")
    subscription_tier: Optional[str] = Field(default=None, alias="subscriptionTier")
    is_upgraded: bool = Field(default=False, alias="isUpgraded")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
