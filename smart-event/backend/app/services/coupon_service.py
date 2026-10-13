from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import Tuple, Optional
from app.models.coupon import Coupon, DiscountType

def validate_coupon_and_calculate_discount(
    db: Session,
    coupon_code: str,
    booking_amount: float
) -> Tuple[Coupon, float, float]:
    """
    Validates a coupon code against a booking subtotal and returns
    (coupon, discount_amount, final_amount).
    """
    normalized_code = coupon_code.strip().upper()
    coupon = db.query(Coupon).filter(Coupon.coupon_code == normalized_code).first()

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )

    if not coupon.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon is inactive"
        )

    if coupon.expiry_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon has expired"
        )

    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon usage limit has been reached"
        )

    if float(booking_amount) < float(coupon.minimum_booking_amount):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking amount must be at least {coupon.minimum_booking_amount} to use this coupon"
        )

    subtotal = float(booking_amount)
    if coupon.discount_type == DiscountType.PERCENTAGE:
        discount_val = float(coupon.discount_value)
        if discount_val <= 0 or discount_val > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid percentage discount value")
        discount_amount = round(subtotal * (discount_val / 100.0), 2)
    elif coupon.discount_type == DiscountType.FIXED:
        discount_val = float(coupon.discount_value)
        if discount_val <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid fixed discount value")
        discount_amount = min(subtotal, round(discount_val, 2))
    else:
        discount_amount = 0.0

    final_amount = max(0.0, round(subtotal - discount_amount, 2))
    return coupon, discount_amount, final_amount

def consume_coupon_atomic(db: Session, coupon_id: int):
    """
    Safely increments coupon used_count inside an active transaction.
    Uses with_for_update() to prevent race conditions.
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).with_for_update().first()
    if not coupon:
        return
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon usage limit reached during checkout"
        )
    coupon.used_count += 1
    db.flush()
