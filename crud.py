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
    Order, OrderItem, OrderCreate, OrderItemCreate,
    Cart, CartItem, CartItemCreate, CartItemUpdate
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


def update_order_payment_status(
    session: Session,
    order_id: int,
    payment_status: str,
    stripe_payment_intent_id: Optional[str] = None
) -> Optional[Order]:
    """Update payment status of an order.
    
    Args:
        session: Database session
        order_id: Order ID to update
        payment_status: New payment status (pending, paid, failed)
        stripe_payment_intent_id: Optional Stripe payment intent ID
    
    Returns:
        Updated Order or None if not found
    """
    order = session.get(Order, order_id)
    if not order:
        return None
    
    order.payment_status = payment_status
    if stripe_payment_intent_id:
        order.stripe_payment_intent_id = stripe_payment_intent_id
    
    # Update order status based on payment status
    if payment_status == "paid":
        order.status = "confirmed"
    elif payment_status == "failed":
        order.status = "cancelled"
    
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def get_order_by_stripe_payment_intent(
    session: Session,
    stripe_payment_intent_id: str
) -> Optional[Order]:
    """Get an order by Stripe payment intent ID."""
    stmt = select(Order).where(Order.stripe_payment_intent_id == stripe_payment_intent_id)
    return session.exec(stmt).first()


# -------- Cart operations --------
def get_or_create_cart(session: Session, user_id: int) -> Cart:
    """Get or create a cart for a user."""
    stmt = select(Cart).where(Cart.user_id == user_id)
    cart = session.exec(stmt).first()
    
    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        session.commit()
        session.refresh(cart)
    
    return cart


def get_cart(session: Session, cart_id: int) -> Optional[Cart]:
    """Get a cart by id."""
    return session.get(Cart, cart_id)


def get_cart_by_user(session: Session, user_id: int) -> Optional[Cart]:
    """Get a cart by user_id."""
    stmt = select(Cart).where(Cart.user_id == user_id)
    return session.exec(stmt).first()


def add_to_cart(session: Session, cart_id: int, item_in: CartItemCreate) -> CartItem:
    """Add an item to the cart or update quantity if it already exists."""
    # Check if product exists
    product = get_product(session, item_in.product_id)
    if not product:
        raise ValueError(f"Product with id {item_in.product_id} not found")
    
    # Check if item already in cart
    stmt = select(CartItem).where(
        CartItem.cart_id == cart_id,
        CartItem.product_id == item_in.product_id
    )
    existing_item = session.exec(stmt).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += item_in.quantity
        session.add(existing_item)
    else:
        # Create new item
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        session.add(cart_item)
    
    # Update cart's updated_at timestamp
    cart = session.get(Cart, cart_id)
    if cart:
        from datetime import datetime, timezone
        cart.updated_at = datetime.now(timezone.utc)
        session.add(cart)
    
    session.commit()
    return existing_item if existing_item else session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == item_in.product_id
        )
    ).first()


def update_cart_item(session: Session, cart_item_id: int, item_in: CartItemUpdate) -> Optional[CartItem]:
    """Update the quantity of a cart item."""
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item:
        return None
    
    cart_item.quantity = item_in.quantity
    session.add(cart_item)
    
    # Update cart's updated_at timestamp
    cart = session.get(Cart, cart_item.cart_id)
    if cart:
        from datetime import datetime, timezone
        cart.updated_at = datetime.now(timezone.utc)
        session.add(cart)
    
    session.commit()
    session.refresh(cart_item)
    return cart_item


def remove_from_cart(session: Session, cart_item_id: int) -> bool:
    """Remove an item from the cart. Returns True if deleted, False if not found."""
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item:
        return False
    
    # Update cart's updated_at timestamp
    cart = session.get(Cart, cart_item.cart_id)
    if cart:
        from datetime import datetime, timezone
        cart.updated_at = datetime.now(timezone.utc)
        session.add(cart)
    
    session.delete(cart_item)
    session.commit()
    return True


def get_cart_items(session: Session, cart_id: int) -> List[CartItem]:
    """Get all items in a cart."""
    stmt = select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.added_at.desc())
    return session.exec(stmt).all()


def clear_cart(session: Session, cart_id: int) -> bool:
    """Clear all items from a cart. Returns True if successful."""
    stmt = select(CartItem).where(CartItem.cart_id == cart_id)
    items = session.exec(stmt).all()
    
    for item in items:
        session.delete(item)
    
    # Update cart's updated_at timestamp
    cart = session.get(Cart, cart_id)
    if cart:
        from datetime import datetime, timezone
        cart.updated_at = datetime.now(timezone.utc)
        session.add(cart)
    
    session.commit()
    return True


def cart_to_order(session: Session, user_id: int, cart_id: int) -> Order:
    """Convert cart items to an order. Clears the cart after successful order creation.
    
    Validates product availability, calculates total price, and updates stock.
    Returns the created Order.
    
    Raises:
        ValueError: If cart is empty, product not found, or insufficient stock
    """
    cart_items = get_cart_items(session, cart_id)
    
    if not cart_items:
        raise ValueError("Cart is empty")
    
    total_price = Decimal("0.00")
    order_items = []
    
    # Validate all products and calculate total
    for cart_item in cart_items:
        product = get_product(session, cart_item.product_id)
        if not product:
            raise ValueError(f"Product with id {cart_item.product_id} not found")
        
        if product.in_stock < cart_item.quantity:
            raise ValueError(
                f"Insufficient stock for product '{product.name}'. "
                f"Available: {product.in_stock}, Requested: {cart_item.quantity}"
            )
        
        item_total = product.price * cart_item.quantity
        total_price += item_total
    
    # Create the order
    order = Order(user_id=user_id, total_price=total_price, status="pending")
    session.add(order)
    session.flush()  # Flush to get order.id without committing
    
    # Create order items and update stock
    for cart_item in cart_items:
        product = get_product(session, cart_item.product_id)
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=product.price
        )
        session.add(order_item)
        order_items.append(order_item)
        
        # Update product stock
        product.in_stock -= cart_item.quantity
        session.add(product)
    
    # Clear the cart
    clear_cart(session, cart_id)
    
    session.commit()
    session.refresh(order)
    
    # Refresh order items
    for item in order_items:
        session.refresh(item)
    
    return order
