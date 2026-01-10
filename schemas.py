"""Pydantic schemas for API request/response validation."""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import ConfigDict, Field

# -------- User Schemas --------
class UserCreate:
    """Schema for creating a new user (plaintext password expected)."""
    full_name: str
    email: str
    password: str


class UserRead:
    """Schema returned in responses for users."""
    id: int
    full_name: str
    email: str
    contact: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

    model_config = ConfigDict(from_attributes=True)


# -------- Product Schemas --------
class ProductCreate:
    """Schema for creating a new product."""
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal("0.00")
    in_stock: int = 0
    category: Optional[str] = None
    media_url: Optional[str] = None


class ProductUpdate:
    """Schema for updating a product (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    in_stock: Optional[int] = None
    category: Optional[str] = None
    media_url: Optional[str] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None


class ProductRead:
    """Schema returned in responses for products."""
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    in_stock: int
    category: Optional[str] = None
    media_url: Optional[str] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# -------- Order Schemas --------
class OrderItemCreate:
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate:
    items: List[OrderItemCreate]


class OrderItemRead:
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class OrderRead:
    id: int
    user_id: int
    created_at: datetime
    status: str
    total_price: Decimal
    payment_status: str
    stripe_payment_intent_id: Optional[str] = None
    items: Optional[List[OrderItemRead]] = None
    
    model_config = ConfigDict(from_attributes=True)


# -------- Cart Schemas --------
class CartItemCreate:
    """Schema for adding items to cart."""
    product_id: int
    quantity: int = Field(gt=0)


class CartItemUpdate:
    """Schema for updating cart item quantity."""
    quantity: int = Field(gt=0)


class CartItemRead:
    """Schema for cart items in responses."""
    id: int
    product_id: int
    quantity: int
    added_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartRead:
    """Schema for cart responses with items."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: Optional[List[CartItemRead]] = None
    
    model_config = ConfigDict(from_attributes=True)
