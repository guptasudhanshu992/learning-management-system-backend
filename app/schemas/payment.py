from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Payment Schemas
class StripePaymentIntent(BaseModel):
    amount: int  # Amount in cents
    currency: str = "usd"
    order_id: Optional[int] = None

class StripePaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str

class RazorpayOrder(BaseModel):
    amount: int  # Amount in smallest currency unit (paisa for INR)
    currency: str = "INR"
    order_id: Optional[int] = None

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key: str

class PaymentVerification(BaseModel):
    payment_id: str
    order_id: Optional[str] = None
    signature: Optional[str] = None  # For Razorpay

class PaymentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None