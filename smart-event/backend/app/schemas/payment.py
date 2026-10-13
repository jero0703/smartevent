from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentStatus

class PaymentCheckoutRequest(BaseModel):
    booking_id: int
    payment_method: Optional[str] = "simulation"

class PaymentSimulateRequest(BaseModel):
    status: PaymentStatus
    transaction_id: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    payment_method: str
    payment_status: PaymentStatus
    transaction_id: Optional[str] = None
    amount: float
    created_at: datetime
    checkout_url: Optional[str] = None
    message: Optional[str] = None

    model_config = {"from_attributes": True}

class PaymentWebhookResponse(BaseModel):
    status: str
    message: Optional[str] = None
