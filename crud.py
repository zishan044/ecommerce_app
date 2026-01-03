"""Simple CRUD helpers for the app's models.

Functions accept a SQLModel `Session` and schema/model inputs and return
model instances or lists.
"""
from typing import List, Optional
from decimal import Decimal

from passlib.context import CryptContext
from sqlmodel import Session, select

from models import (
    Product, User, ProductCreate, ProductUpdate, UserCreate,
    Order, OrderItem, OrderCreate, OrderItemCreate
)

# Create a password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    """Return a bcrypt hash of the password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


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


def update_product(session: Session, product_id: int, product_in: ProductUpdate) -> Optional[Product]:
    """Update a Product by id and return it, or None if not found."""
    product = session.get(Product, product_id)
    if not product:
        return None
    
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, product_id: int) -> bool:
    """Delete a Product by id. Returns True if deleted, False if not found."""
    product = session.get(Product, product_id)
    if not product:
        return False
    
    session.delete(product)
    session.commit()
    return True


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


# -------- Order operations --------
def create_order(session: Session, user_id: int, order_in: OrderCreate) -> Order:
    """Create an Order with OrderItems from the `OrderCreate` schema.
    
    Validates product availability, calculates total price, and updates stock.
    Returns the created Order.
    
    Raises:
        ValueError: If a product is not found or insufficient stock available
    """
    total_price = Decimal("0.00")
    order_items = []
    
    # Validate all products and calculate total
    for item_create in order_in.items:
        product = get_product(session, item_create.product_id)
        if not product:
            raise ValueError(f"Product with id {item_create.product_id} not found")
        
        if product.in_stock < item_create.quantity:
            raise ValueError(
                f"Insufficient stock for product '{product.name}'. "
                f"Available: {product.in_stock}, Requested: {item_create.quantity}"
            )
        
        item_total = product.price * item_create.quantity
        total_price += item_total
    
    # Create the order
    order = Order(user_id=user_id, total_price=total_price, status="pending")
    session.add(order)
    session.flush()  # Flush to get order.id without committing
    
    # Create order items and update stock
    for item_create in order_in.items:
        product = get_product(session, item_create.product_id)
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_create.product_id,
            quantity=item_create.quantity,
            unit_price=product.price
        )
        session.add(order_item)
        order_items.append(order_item)
        
        # Update product stock
        product.in_stock -= item_create.quantity
        session.add(product)
    
    session.commit()
    session.refresh(order)
    
    # Refresh order items
    for item in order_items:
        session.refresh(item)
    
    return order


def get_order(session: Session, order_id: int) -> Optional[Order]:
    """Return an Order by id or None if not found."""
    return session.get(Order, order_id)


def get_orders_by_user(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    """Return orders for a specific user with optional pagination."""
    stmt = select(Order).where(Order.user_id == user_id).offset(skip).limit(limit).order_by(Order.created_at.desc())
    return session.exec(stmt).all()


def get_all_orders(session: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    """Return all orders with optional pagination."""
    stmt = select(Order).offset(skip).limit(limit).order_by(Order.created_at.desc())
    return session.exec(stmt).all()


def get_order_items(session: Session, order_id: int) -> List[OrderItem]:
    """Return all OrderItems for a specific order."""
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    return session.exec(stmt).all()
