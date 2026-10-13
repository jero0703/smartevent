from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.coupon import Coupon
from app.models.booking import Booking
from app.models.event import Event
from app.schemas.coupon import (
    CouponCreate,
    CouponUpdate,
    CouponResponse,
    CouponValidateRequest,
    CouponValidateResponse
)
from app.utils.dependencies import require_admin
from app.services.coupon_service import validate_coupon_and_calculate_discount

router = APIRouter(prefix="/coupons", tags=["Coupons"])

@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon_endpoint(
    req: CouponValidateRequest,
    db: Session = Depends(get_db)
):
    subtotal = 0.0
    if req.booking_amount is not None:
        subtotal = float(req.booking_amount)
    elif req.booking_id is not None:
        booking = db.query(Booking).filter(Booking.id == req.booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        subtotal = float(booking.total_price)
    elif req.event_id is not None:
        event = db.query(Event).filter(Event.id == req.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        subtotal = float(event.ticket_price) * (req.ticket_quantity or 1)
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide booking_amount, booking_id, or event_id to validate coupon"
        )

    coupon, discount_amount, final_amount = validate_coupon_and_calculate_discount(
        db=db,
        coupon_code=req.coupon_code,
        booking_amount=subtotal
    )

    return {
        "valid": True,
        "coupon_code": coupon.coupon_code,
        "discount_type": coupon.discount_type,
        "discount_value": float(coupon.discount_value),
        "original_amount": subtotal,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "message": "Coupon applied successfully"
    }

@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    coupon_in: CouponCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    normalized_code = coupon_in.coupon_code.strip().upper()
    existing = db.query(Coupon).filter(Coupon.coupon_code == normalized_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A coupon with this code already exists"
        )

    coupon = Coupon(
        coupon_code=normalized_code,
        discount_type=coupon_in.discount_type,
        discount_value=coupon_in.discount_value,
        minimum_booking_amount=coupon_in.minimum_booking_amount,
        expiry_date=coupon_in.expiry_date,
        usage_limit=coupon_in.usage_limit,
        is_active=coupon_in.is_active
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

@router.get("", response_model=List[CouponResponse])
def list_coupons(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    return db.query(Coupon).offset((page - 1) * limit).limit(limit).all()

@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon

@router.patch("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    coupon_update: CouponUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    update_data = coupon_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(coupon, field, value)

    db.commit()
    db.refresh(coupon)
    return coupon

@router.patch("/{coupon_id}/deactivate", response_model=CouponResponse)
def deactivate_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.is_active = False
    db.commit()
    db.refresh(coupon)
    return coupon
