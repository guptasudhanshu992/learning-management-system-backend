from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.db.database import get_db
from app.db import models
from app.schemas.payment import (
    StripePaymentIntent, StripePaymentIntentResponse,
    RazorpayOrder, RazorpayOrderResponse,
    PaymentVerification, PaymentResponse
)
from app.core.auth import get_current_active_user
from app.services import stripe_service, razorpay_service

# Create router
router = APIRouter()

@router.post("/stripe/create-intent", response_model=StripePaymentIntentResponse)
def create_stripe_payment_intent(
    payment_intent_data: StripePaymentIntent,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Create payment intent with Stripe
    """
    try:
        # Create payment intent
        payment_intent = stripe_service.create_payment_intent(payment_intent_data)
        
        return payment_intent
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/stripe/verify", response_model=PaymentResponse)
def verify_stripe_payment(
    verification_data: PaymentVerification,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Verify Stripe payment and complete order
    """
    try:
        # Verify payment
        payment_verified = stripe_service.verify_payment_intent(verification_data.payment_id)
        
        if not payment_verified:
            return PaymentResponse(
                success=False,
                message="Payment verification failed"
            )
        
        # Update order if order_id is provided
        if verification_data.order_id:
            # Convert string order ID to int
            try:
                order_id = int(verification_data.order_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid order ID"
                )
            
            # Get order
            order = db.query(models.Order).filter(models.Order.id == order_id).first()
            
            if order and order.user_id == current_user.id:
                # Update order status
                order.payment_status = "completed"
                order.payment_id = verification_data.payment_id
                db.commit()
                
                # Create enrollments for each course in the order
                create_enrollments_from_order(order, db)
                
                # Clear user's cart
                db.query(models.CartItem).filter(
                    models.CartItem.user_id == current_user.id
                ).delete()
                
                db.commit()
        
        return PaymentResponse(
            success=True,
            message="Payment verified successfully",
            data={"payment_id": verification_data.payment_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/razorpay/create-order", response_model=RazorpayOrderResponse)
def create_razorpay_order(
    order_data: RazorpayOrder,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Create order with Razorpay
    """
    try:
        # Create Razorpay order
        razorpay_order = razorpay_service.create_order(order_data)
        
        return razorpay_order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/razorpay/verify", response_model=PaymentResponse)
def verify_razorpay_payment(
    verification_data: PaymentVerification,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Verify Razorpay payment and complete order
    """
    try:
        # Verify payment signature
        if not verification_data.order_id or not verification_data.signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order ID and signature are required"
            )
        
        payment_verified = razorpay_service.verify_payment_signature(
            verification_data.payment_id,
            verification_data.order_id,
            verification_data.signature
        )
        
        if not payment_verified:
            return PaymentResponse(
                success=False,
                message="Payment signature verification failed"
            )
        
        # Get payment details
        payment_details = razorpay_service.fetch_payment(verification_data.payment_id)
        
        # Update order if order_id is provided in metadata
        receipt = payment_details.get("receipt")
        if receipt and receipt.startswith("order_"):
            try:
                order_id = int(receipt[6:])  # Extract ID from "order_123"
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid order ID in receipt"
                )
            
            # Get order
            order = db.query(models.Order).filter(models.Order.id == order_id).first()
            
            if order and order.user_id == current_user.id:
                # Update order status
                order.payment_status = "completed"
                order.payment_id = verification_data.payment_id
                db.commit()
                
                # Create enrollments for each course in the order
                create_enrollments_from_order(order, db)
                
                # Clear user's cart
                db.query(models.CartItem).filter(
                    models.CartItem.user_id == current_user.id
                ).delete()
                
                db.commit()
        
        return PaymentResponse(
            success=True,
            message="Payment verified successfully",
            data={"payment_id": verification_data.payment_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Helper function to create enrollments from an order
def create_enrollments_from_order(order: models.Order, db: Session):
    """
    Create enrollments for each course in the order
    """
    from datetime import datetime
    
    for item in order.order_items:
        # Check if user is already enrolled
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.user_id == order.user_id,
            models.Enrollment.course_id == item.course_id
        ).first()
        
        if not enrollment:
            # Create new enrollment
            new_enrollment = models.Enrollment(
                user_id=order.user_id,
                course_id=item.course_id,
                enrollment_date=datetime.utcnow(),
                progress_percentage=0.0,
                certificate_issued=False
            )
            
            db.add(new_enrollment)
    
    db.commit()