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
    items: Optional[List[OrderItemRead]] = None
    
    model_config = ConfigDict(from_attributes=True)