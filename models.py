from typing import Optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from pydantic import ConfigDict
from datetime import datetime, timezone
from typing import List

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: Decimal = Field(default=Decimal("0.00"))
    in_stock: int = Field(default=0)
    category: Optional[str] = None
    media_url: Optional[str] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    contact: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class UserCreate(SQLModel):
    """Schema for creating a new user (plaintext password expected)."""
    full_name: str
    email: str
    password: str


class UserRead(SQLModel):
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


class ProductCreate(SQLModel):
    """Schema for creating a new product."""
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal("0.00")
    in_stock: int = 0
    category: Optional[str] = None
    media_url: Optional[str] = None


class ProductUpdate(SQLModel):
    """Schema for updating a product (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    in_stock: Optional[int] = None
    category: Optional[str] = None
    media_url: Optional[str] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None


class ProductRead(SQLModel):
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

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending")
    total_price: Decimal = Field(default=Decimal("0.00"))
    payment_status: str = Field(default="pending")  # pending, paid, failed
    stripe_payment_intent_id: Optional[str] = None

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)
    unit_price: Decimal = Field(default=Decimal("0.00"))

class OrderItemCreate(SQLModel):
    product_id: int
    quantity: int = Field(gt=0)

class OrderCreate(SQLModel):
    items: List[OrderItemCreate]

class OrderItemRead(SQLModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class OrderRead(SQLModel):
    id: int
    user_id: int
    created_at: datetime
    status: str
    total_price: Decimal
    payment_status: str
    stripe_payment_intent_id: Optional[str] = None
    items: Optional[List[OrderItemRead]] = None
    
    model_config = ConfigDict(from_attributes=True)


class Cart(SQLModel, table=True):
    """Shopping cart for a user. Persists across sessions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CartItem(SQLModel, table=True):
    """Items in a user's shopping cart."""
    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="cart.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(gt=0)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CartItemRead(SQLModel):
    """Schema for cart items in responses."""
    id: int
    product_id: int
    quantity: int
    added_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartRead(SQLModel):
    """Schema for cart responses with items."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: Optional[List[CartItemRead]] = None
    
    model_config = ConfigDict(from_attributes=True)


class CartItemCreate(SQLModel):
    """Schema for adding items to cart."""
    product_id: int
    quantity: int = Field(gt=0)


class CartItemUpdate(SQLModel):
    """Schema for updating cart item quantity."""
    quantity: int = Field(gt=0)