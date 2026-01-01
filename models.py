from typing import Optional
from sqlmodel import SQLModel, Field
from decimal import Decimal

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: Decimal = Field(default=0, max_digits=10, decimal_places=2)
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

    class Config:
        orm_mode = True


class ProductCreate(SQLModel):
    """Schema for creating a new product."""
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal("0.00")
    in_stock: int = 0
    category: Optional[str] = None
    media_url: Optional[str] = None


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

    class Config:
        orm_mode = True
