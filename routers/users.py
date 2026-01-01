from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud
from database import get_session
from models import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(*, user_in: UserCreate, session: Session = Depends(get_session)):
    """Register a new user."""
    existing = crud.get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(session, user_in)
