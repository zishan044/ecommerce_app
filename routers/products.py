from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud
from database import get_session
from models import Product, ProductCreate, ProductRead, ProductUpdate, User
from security import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductRead])
def read_products(*, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """Return a list of products."""
    return crud.get_products(session, skip=skip, limit=limit)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    *,
    product_in: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new product. Requires authentication."""
    return crud.create_product(session, product_in)


@router.get("/{product_id}", response_model=ProductRead)
def read_product(*, product_id: int, session: Session = Depends(get_session)):
    """Return a single product by id."""
    product = crud.get_product(session, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    *,
    product_id: int,
    product_in: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a product by id. Requires authentication."""
    product = crud.update_product(session, product_id, product_in)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    *,
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a product by id. Requires authentication."""
    deleted = crud.delete_product(session, product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return None
