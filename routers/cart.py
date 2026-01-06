"""Shopping cart routes."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud
from database import get_session
from models import Cart, CartItem, CartItemCreate, CartItemRead, CartRead, User
from security import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
def get_cart(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's cart with all items."""
    cart = crud.get_or_create_cart(session, current_user.id)
    
    # Fetch cart items
    cart_items = crud.get_cart_items(session, cart.id)
    cart_dict = cart.model_dump()
    cart_dict["items"] = [item.model_dump() for item in cart_items]
    
    return CartRead(**cart_dict)


@router.post("/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    *,
    item_in: CartItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add an item to the cart or increment quantity if it already exists.
    
    Requires authentication. Product must exist.
    """
    try:
        # Get or create cart
        cart = crud.get_or_create_cart(session, current_user.id)
        
        # Add item to cart
        cart_item = crud.add_to_cart(session, cart.id, item_in)
        
        return CartItemRead(
            id=cart_item.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            added_at=cart_item.added_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/items/{cart_item_id}", response_model=CartItemRead)
def update_cart_item(
    *,
    cart_item_id: int,
    item_in: CartItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update the quantity of a cart item.
    
    Requires authentication. User must own the cart.
    """
    # Get the cart item
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    # Get the cart
    cart = session.get(Cart, cart_item.cart_id)
    if not cart or cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this cart"
        )
    
    # Update item
    from models import CartItemUpdate
    updated_item = crud.update_cart_item(session, cart_item_id, CartItemUpdate(quantity=item_in.quantity))
    
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    return CartItemRead(
        id=updated_item.id,
        product_id=updated_item.product_id,
        quantity=updated_item.quantity,
        added_at=updated_item.added_at
    )


@router.delete("/items/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    *,
    cart_item_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Remove an item from the cart.
    
    Requires authentication. User must own the cart.
    """
    # Get the cart item
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    # Get the cart
    cart = session.get(Cart, cart_item.cart_id)
    if not cart or cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this cart"
        )
    
    # Remove item
    deleted = crud.remove_from_cart(session, cart_item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Clear all items from the user's cart.
    
    Requires authentication.
    """
    cart = crud.get_cart_by_user(session, current_user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    crud.clear_cart(session, cart.id)
    return None
