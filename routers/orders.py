from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud
from database import get_session
from models import Order, OrderCreate, OrderRead, OrderItem, OrderItemRead, User
from security import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    *,
    order_in: OrderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new order (checkout). Requires authentication.
    
    Validates product availability, calculates total price, and updates stock.
    """
    try:
        order = crud.create_order(session, current_user.id, order_in)
        
        # Fetch order items to include in response
        order_items = crud.get_order_items(session, order.id)
        order_dict = order.model_dump()
        order_dict["items"] = [item.model_dump() for item in order_items]
        
        return OrderRead(**order_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[OrderRead])
def get_orders(
    *,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get orders for the current authenticated user."""
    orders = crud.get_orders_by_user(session, current_user.id, skip=skip, limit=limit)
    
    # Include order items for each order
    result = []
    for order in orders:
        order_items = crud.get_order_items(session, order.id)
        order_dict = order.model_dump()
        order_dict["items"] = [item.model_dump() for item in order_items]
        result.append(OrderRead(**order_dict))
    
    return result


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    *,
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific order by id. Users can only access their own orders."""
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
    
    # Fetch order items
    order_items = crud.get_order_items(session, order.id)
    order_dict = order.model_dump()
    order_dict["items"] = [item.model_dump() for item in order_items]
    
    return OrderRead(**order_dict)

