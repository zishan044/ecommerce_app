from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud
from database import get_session
from models import ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductRead])
def read_products(*, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """Return a list of products."""
    return crud.get_products(session, skip=skip, limit=limit)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(*, product_in: ProductCreate, session: Session = Depends(get_session)):
    """Create a new product."""
    return crud.create_product(session, product_in)


@router.get("/{product_id}", response_model=ProductRead)
def read_product(*, product_id: int, session: Session = Depends(get_session)):
    """Return a single product by id."""
    product = crud.get_product(session, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
