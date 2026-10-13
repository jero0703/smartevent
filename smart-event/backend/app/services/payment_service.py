from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, Tuple
import uuid
from app.models.payment import Payment, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.models.notification import NotificationType
from app.core.config import settings
from app.utils.qr_generator import generate_qr_code
from app.services.notification_service import create_notification
from app.services.coupon_service import consume_coupon_atomic

def initiate_checkout(
    db: Session,
    user: User,
    booking_id: int,
    payment_method: str = "simulation"
) -> Tuple[Payment, Optional[str]]:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to checkout this booking"
        )

    if booking.booking_status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay for a cancelled booking"
        )

    # Check if booking is already successfully paid
    existing_success = db.query(Payment).filter(
        Payment.booking_id == booking.id,
        Payment.payment_status == PaymentStatus.SUCCESS
    ).first()
    if existing_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has already been paid for"
        )

    # Calculate payable amount from server-side final_amount / total_price
    payable_amount = float(booking.final_amount if booking.final_amount is not None else booking.total_price)

    # Handle Stripe Checkout if configured
    if settings.PAYMENT_PROVIDER == "stripe" and settings.STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Tickets for {booking.event.title}",
                        },
                        "unit_amount": int(round(payable_amount * 100)),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.STRIPE_CANCEL_URL,
                metadata={"booking_id": str(booking.id), "user_id": str(user.id)},
            )
            
            payment = Payment(
                booking_id=booking.id,
                payment_method="STRIPE",
                payment_status=PaymentStatus.PENDING,
                transaction_id=session.id,
                amount=payable_amount
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return payment, session.url
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe initialization failed: {str(e)}"
            )

    # Default / Simulator checkout
    txn_ref = f"SIM-TXN-{uuid.uuid4().hex[:12].upper()}"
    payment = Payment(
        booking_id=booking.id,
        payment_method=payment_method or "simulation",
        payment_status=PaymentStatus.PENDING,
        transaction_id=txn_ref,
        amount=payable_amount
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment, None

def process_payment_success(
    db: Session,
    payment: Payment,
    transaction_id: Optional[str] = None
) -> Payment:
    # Idempotent check
    if payment.payment_status == PaymentStatus.SUCCESS:
        return payment

    # Prevent multiple successful charges for the same booking
    other_paid = db.query(Payment).filter(
        Payment.booking_id == payment.booking_id,
        Payment.payment_status == PaymentStatus.SUCCESS,
        Payment.id != payment.id
    ).first()
    if other_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has already been paid for by another transaction"
        )

    payment.payment_status = PaymentStatus.SUCCESS
    if transaction_id:
        payment.transaction_id = transaction_id

    booking = payment.booking
    booking.booking_status = BookingStatus.CONFIRMED

    # Consume coupon atomically if present
    if booking.coupon_id:
        consume_coupon_atomic(db, booking.coupon_id)

    # Generate QR ticket if not already generated
    if not booking.ticket:
        ticket_code = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        qr_url = generate_qr_code(ticket_code, booking.id)
        ticket = Ticket(
            booking_id=booking.id,
            ticket_code=ticket_code,
            qr_code_url=qr_url
        )
        db.add(ticket)

    # Create notifications
    create_notification(
        db=db,
        user_id=booking.user_id,
        title="Payment Successful",
        message=f"Your payment of ${float(payment.amount):.2f} for booking #{booking.id} was successful.",
        type=NotificationType.PAYMENT
    )
    create_notification(
        db=db,
        user_id=booking.user_id,
        title="Booking Confirmed",
        message=f"Your booking for {booking.event.title} has been confirmed.",
        type=NotificationType.BOOKING
    )

    db.commit()
    db.refresh(payment)
    return payment

def process_payment_failure(
    db: Session,
    payment: Payment,
    reason: Optional[str] = None
) -> Payment:
    if payment.payment_status == PaymentStatus.FAILED:
        return payment

    if payment.payment_status == PaymentStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark an already successful payment as failed"
        )

    payment.payment_status = PaymentStatus.FAILED
    booking = payment.booking

    create_notification(
        db=db,
        user_id=booking.user_id,
        title="Payment Failed",
        message=f"Your payment of ${float(payment.amount):.2f} for booking #{booking.id} failed. {reason or ''}".strip(),
        type=NotificationType.PAYMENT
    )

    db.commit()
    db.refresh(payment)
    return payment

def simulate_payment_result(
    db: Session,
    user: User,
    payment_id: int,
    status_choice: PaymentStatus,
    transaction_id: Optional[str] = None
) -> Payment:
    if not settings.PAYMENT_SIMULATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment simulation is disabled in this environment"
        )

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )

    if payment.booking.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to simulate this payment"
        )

    if status_choice == PaymentStatus.SUCCESS:
        return process_payment_success(db, payment, transaction_id)
    else:
        return process_payment_failure(db, payment, "Simulated failure")
