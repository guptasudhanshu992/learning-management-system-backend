import os
import stripe
from app.schemas.payment import StripePaymentIntent, StripePaymentIntentResponse

# Initialize Stripe with your secret key
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "your-stripe-secret-key")

def create_payment_intent(payment_data: StripePaymentIntent) -> StripePaymentIntentResponse:
    """
    Create a payment intent with Stripe
    """
    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=payment_data.amount,
            currency=payment_data.currency,
            metadata={
                'order_id': payment_data.order_id
            },
            automatic_payment_methods={
                'enabled': True,
            },
        )
        
        return StripePaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id
        )
    except Exception as e:
        raise Exception(f"Error creating payment intent: {str(e)}")

def verify_payment_intent(payment_intent_id: str) -> bool:
    """
    Verify a payment intent with Stripe
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        return intent.status == "succeeded"
    except Exception as e:
        raise Exception(f"Error verifying payment: {str(e)}")

def refund_payment(payment_intent_id: str) -> dict:
    """
    Refund a payment with Stripe
    """
    try:
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id
        )
        
        return {
            "success": refund.status == "succeeded",
            "id": refund.id,
            "status": refund.status
        }
    except Exception as e:
        raise Exception(f"Error refunding payment: {str(e)}")