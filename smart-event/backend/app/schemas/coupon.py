from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.coupon import DiscountType

class CouponBase(BaseModel):
    coupon_code: str = Field(..., min_length=2, max_length=50)
    discount_type: DiscountType
    discount_value: float = Field(..., gt=0)
    minimum_booking_amount: float = Field(default=0.0, ge=0)
    expiry_date: datetime
    usage_limit: Optional[int] = Field(default=None, gt=0)
    is_active: bool = True

    @field_validator("coupon_code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

class CouponCreate(CouponBase):
    @field_validator("discount_value")
    @classmethod
    def validate_discount(cls, v: float, info):
        discount_type = info.data.get("discount_type")
        if discount_type == DiscountType.PERCENTAGE and v > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
        return v

class CouponUpdate(BaseModel):
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = Field(default=None, gt=0)
    minimum_booking_amount: Optional[float] = Field(default=None, ge=0)
    expiry_date: Optional[datetime] = None
    usage_limit: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None

class CouponResponse(CouponBase):
    id: int
    used_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

class CouponValidateRequest(BaseModel):
    coupon_code: str
    booking_amount: Optional[float] = Field(default=None, ge=0)
    booking_id: Optional[int] = None
    event_id: Optional[int] = None
    ticket_quantity: Optional[int] = Field(default=1, gt=0)

    @field_validator("coupon_code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

class CouponValidateResponse(BaseModel):
    valid: bool
    coupon_code: str
    discount_type: DiscountType
    discount_value: float
    original_amount: float
    discount_amount: float
    final_amount: float
    message: str
