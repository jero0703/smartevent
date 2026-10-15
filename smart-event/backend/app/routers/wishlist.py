from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.event import Event
from app.models.wishlist import Wishlist
from app.schemas.wishlist import (
    WishlistItemResponse,
    PaginatedWishlistResponse,
    WishlistStatusResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])

@router.post("/{event_id}", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.event_id == event_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event is already in your wishlist"
        )

    item = Wishlist(user_id=current_user.id, event_id=event_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def remove_from_wishlist(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.event_id == event_id
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found in your wishlist"
        )

    db.delete(item)
    db.commit()
    return {"message": "Event removed from wishlist", "event_id": event_id}

@router.get("", response_model=PaginatedWishlistResponse)
def get_my_wishlist(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).order_by(Wishlist.created_at.desc())
    total = query.count()
    pages = (total + limit - 1) // limit if total > 0 else 0
    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "total_pages": pages
    }

@router.get("/{event_id}/status", response_model=WishlistStatusResponse)
def get_wishlist_status(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.event_id == event_id
    ).first()
    return {
        "event_id": event_id,
        "is_saved": item is not None
    }
