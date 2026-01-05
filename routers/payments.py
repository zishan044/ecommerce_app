"""Payment routes for Stripe integration."""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlmodel import Session
import stripe
from dotenv import load_dotenv

import crud
from database import get_session
from models import User, Order
from security import get_current_user

load_dotenv()

router = APIRouter(prefix="/payments", tags=["payments"])

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not STRIPE_SECRET_KEY:
    raise ValueError("STRIPE_SECRET_KEY environment variable is not set")

stripe.api_key = STRIPE_SECRET_KEY


@router.post("/create-checkout-session/{order_id}")
def create_checkout_session(
    *,
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe checkout session for an order.
    
    Requires authentication. Users can only create checkout sessions for their own orders.
    """
    # Get the order
    order = crud.get_order(session, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if user owns this order
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )
    
    # Check if order is already paid
    if order.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid"
        )
    
    # Get order items for line items
    order_items = crud.get_order_items(session, order_id)
    line_items = []
    
    for item in order_items:
        product = crud.get_product(session, item.product_id)
        if not product:
            continue
        
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": product.name,
                    "description": product.description or "",
                },
                "unit_amount": int(float(product.price) * 100),  # Convert to cents
            },
            "quantity": item.quantity,
        })
    
    if not line_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order has no items"
        )
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=os.getenv(
                "STRIPE_SUCCESS_URL",
                f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/orders/{order_id}?success=true"
            ),
            cancel_url=os.getenv(
                "STRIPE_CANCEL_URL",
                f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/orders/{order_id}?canceled=true"
            ),
            metadata={
                "order_id": str(order_id),
                "user_id": str(current_user.id),
            },
            client_reference_id=str(order_id),
        )
        
        # Update order with payment intent ID (for checkout sessions, we'll use session ID)
        # Note: For checkout sessions, we'll track via metadata in webhook
        crud.update_order_payment_status(
            session,
            order_id,
            payment_status="pending",
            stripe_payment_intent_id=checkout_session.payment_intent if hasattr(checkout_session, 'payment_intent') else checkout_session.id
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "order_id": order_id,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
):
    """Handle Stripe webhook events to update order payment status.
    
    This endpoint should be configured in Stripe Dashboard to receive webhook events.
    Webhook URL: https://yourdomain.com/payments/webhook
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured"
        )
    
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}"
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signature: {str(e)}"
        )
    
    # Get database session for webhook processing
    from database import get_session
    db_gen = get_session()
    session = next(db_gen)
    
    try:
        # Handle the event
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        if event_type == "checkout.session.completed":
            # Payment was successful
            session_id = event_data.get("id")
            order_id = event_data.get("metadata", {}).get("order_id")
            payment_intent_id = event_data.get("payment_intent")
            
            if order_id:
                order = crud.update_order_payment_status(
                    session,
                    int(order_id),
                    payment_status="paid",
                    stripe_payment_intent_id=payment_intent_id
                )
                if order:
                    return {"status": "success", "order_id": order_id, "message": "Order payment confirmed"}
        
        elif event_type == "payment_intent.succeeded":
            # Payment intent succeeded (alternative event)
            payment_intent_id = event_data.get("id")
            order = crud.get_order_by_stripe_payment_intent(session, payment_intent_id)
            
            if order:
                crud.update_order_payment_status(
                    session,
                    order.id,
                    payment_status="paid",
                    stripe_payment_intent_id=payment_intent_id
                )
                return {"status": "success", "order_id": order.id, "message": "Order payment confirmed"}
        
        elif event_type == "payment_intent.payment_failed":
            # Payment failed
            payment_intent_id = event_data.get("id")
            order = crud.get_order_by_stripe_payment_intent(session, payment_intent_id)
            
            if order:
                crud.update_order_payment_status(
                    session,
                    order.id,
                    payment_status="failed",
                    stripe_payment_intent_id=payment_intent_id
                )
                return {"status": "success", "order_id": order.id, "message": "Order payment marked as failed"}
        
        elif event_type == "checkout.session.async_payment_failed":
            # Async payment failed
            order_id = event_data.get("metadata", {}).get("order_id")
            if order_id:
                crud.update_order_payment_status(
                    session,
                    int(order_id),
                    payment_status="failed"
                )
                return {"status": "success", "order_id": order_id, "message": "Order payment marked as failed"}
        
        # Return success for unhandled events (so Stripe doesn't retry)
        return {"status": "received", "event_type": event_type}
    finally:
        db_gen.close()

