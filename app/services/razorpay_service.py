import os
import razorpay
from app.schemas.payment import RazorpayOrder, RazorpayOrderResponse

# Initialize Razorpay client with your key and secret
razorpay_client = razorpay.Client(
    auth=(
        os.environ.get("RAZORPAY_KEY_ID", "your-razorpay-key-id"),
        os.environ.get("RAZORPAY_KEY_SECRET", "your-razorpay-key-secret")
    )
)

def create_order(order_data: RazorpayOrder) -> RazorpayOrderResponse:
    """
    Create an order with Razorpay
    """
    try:
        # Create a Razorpay Order
        razorpay_order = razorpay_client.order.create({
            'amount': order_data.amount,
            'currency': order_data.currency,
            'receipt': f"order_{order_data.order_id}" if order_data.order_id else None,
            'payment_capture': '1'  # Auto capture
        })
        
        return RazorpayOrderResponse(
            order_id=razorpay_order['id'],
            amount=razorpay_order['amount'],
            currency=razorpay_order['currency'],
            key=os.environ.get("RAZORPAY_KEY_ID", "your-razorpay-key-id")
        )
    except Exception as e:
        raise Exception(f"Error creating Razorpay order: {str(e)}")

def verify_payment_signature(payment_id: str, order_id: str, signature: str) -> bool:
    """
    Verify Razorpay payment signature
    """
    try:
        # Verify the payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        return razorpay_client.utility.verify_payment_signature(params_dict)
    except Exception:
        return False

def fetch_payment(payment_id: str) -> dict:
    """
    Fetch payment details from Razorpay
    """
    try:
        payment = razorpay_client.payment.fetch(payment_id)
        return payment
    except Exception as e:
        raise Exception(f"Error fetching payment details: {str(e)}")

def refund_payment(payment_id: str) -> dict:
    """
    Refund a payment with Razorpay
    """
    try:
        refund = razorpay_client.payment.refund(payment_id)
        return refund
    except Exception as e:
        raise Exception(f"Error refunding payment: {str(e)}")