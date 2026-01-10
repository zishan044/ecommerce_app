"""SQLModel database table definitions."""
from typing import Optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from datetime import datetime, timezone


class User(SQLModel, table=True):
    """User database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    contact: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class Product(SQLModel, table=True):
    """Product database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: Decimal = Field(default=Decimal("0.00"))
    in_stock: int = Field(default=0)
    category: Optional[str] = None
    media_url: Optional[str] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None


class Order(SQLModel, table=True):
    """Order database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending")
    total_price: Decimal = Field(default=Decimal("0.00"))
    payment_status: str = Field(default="pending")  # pending, paid, failed
    stripe_payment_intent_id: Optional[str] = None


class OrderItem(SQLModel, table=True):
    """Order item database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)
    unit_price: Decimal = Field(default=Decimal("0.00"))


class Cart(SQLModel, table=True):
    """Shopping cart database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CartItem(SQLModel, table=True):
    """Cart item database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="cart.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(gt=0)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))