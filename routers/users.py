from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud
from database import get_session
from models import User
from schemas import UserCreate, UserRead
from security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(*, user_in: UserCreate, session: Session = Depends(get_session)):
    """Register a new user."""
    existing = crud.get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(session, user_in)


@router.get("/me", response_model=UserRead)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user's information."""
    return current_user
