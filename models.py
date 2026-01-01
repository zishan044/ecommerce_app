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
    email: str = Field(unique=True, index=True) # Index makes searching by email faster
    hashed_password: str
    contact: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)