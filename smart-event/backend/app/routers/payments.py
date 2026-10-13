from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.payment import Payment, PaymentStatus
from app.models.booking import Booking
from app.schemas.payment import (
    PaymentCheckoutRequest,
    PaymentSimulateRequest,
    PaymentResponse,
    PaymentWebhookResponse
)
from app.services.auth_service import get_current_user
from app.services.payment_service import (
    initiate_checkout,
    simulate_payment_result,
    process_payment_success,
    process_payment_failure
)
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/checkout", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def checkout_booking(
    req: PaymentCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment, checkout_url = initiate_checkout(
        db=db,
        user=current_user,
        booking_id=req.booking_id,
        payment_method=req.payment_method or "simulation"
    )
    res = PaymentResponse.model_validate(payment)
    res.checkout_url = checkout_url
    if checkout_url:
        res.message = "Redirect to checkout_url to complete payment"
    else:
        res.message = "Payment initiated in simulation mode"
    return res

@router.get("/my", response_model=List[PaymentResponse])
def get_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = db.query(Payment).join(Payment.booking).filter(
        Booking.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).all()
    return payments

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_details(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this payment")

    return payment

@router.post("/{payment_id}/simulate-result", response_model=PaymentResponse)
def simulate_payment_outcome(
    payment_id: int,
    req: PaymentSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = simulate_payment_result(
        db=db,
        user=current_user,
        payment_id=payment_id,
        status_choice=req.status,
        transaction_id=req.transaction_id
    )
    res = PaymentResponse.model_validate(payment)
    res.message = f"Simulated outcome: {payment.payment_status}"
    return res

@router.post("/webhook", response_model=PaymentWebhookResponse)
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if settings.PAYMENT_PROVIDER == "stripe" and settings.STRIPE_WEBHOOK_SECRET:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {str(e)}")

        event_type = event.get("type")
        data_object = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            session_id = data_object.get("id")
            payment = db.query(Payment).filter(Payment.transaction_id == session_id).first()
            if payment:
                process_payment_success(db, payment, session_id)
        elif event_type in ["payment_intent.payment_failed", "charge.failed"]:
            session_id = data_object.get("id")
            payment = db.query(Payment).filter(Payment.transaction_id == session_id).first()
            if payment:
                process_payment_failure(db, payment, "Webhook reported failure")

        return {"status": "success", "message": f"Processed {event_type}"}

    return {"status": "received", "message": "Simulation webhook received"}
