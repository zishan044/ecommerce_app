"""Simple CRUD helpers for the app's models.

Functions accept a SQLModel `Session` and schema/model inputs and return
model instances or lists.
"""
from typing import List, Optional

from passlib.context import CryptContext
from sqlmodel import Session, select

from models import Product, User, ProductCreate, UserCreate

# Create a password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    """Return a bcrypt hash of the password."""
    return pwd_context.hash(password)


# -------- Product operations --------
def get_product(session: Session, product_id: int) -> Optional[Product]:
    """Return a Product by id or None if not found."""
    return session.get(Product, product_id)


def get_products(session: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    """Return multiple products with optional pagination."""
    stmt = select(Product).offset(skip).limit(limit)
    return session.exec(stmt).all()


def create_product(session: Session, product_in: ProductCreate) -> Product:
    """Create a Product from the `ProductCreate` schema and return it."""
    product = Product(**product_in.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


# -------- User operations --------
def get_user(session: Session, user_id: int) -> Optional[User]:
    """Return a User by id or None if not found."""
    return session.get(User, user_id)


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Return a User by email or None if not found."""
    stmt = select(User).where(User.email == email)
    return session.exec(stmt).first()


def get_users(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Return multiple users with optional pagination."""
    stmt = select(User).offset(skip).limit(limit)
    return session.exec(stmt).all()


def create_user(session: Session, user_in: UserCreate) -> User:
    """Create a User from the `UserCreate` schema (hashes password) and return it."""
    hashed = _hash_password(user_in.password)
    user = User(full_name=user_in.full_name, email=user_in.email, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
