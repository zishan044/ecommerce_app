"""Authentication routes for OAuth2 password flow and JWT tokens."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

import crud
from database import get_session
from security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """OAuth2 password flow login endpoint.
    
    Returns a JWT access token if the username (email) and password are correct.
    
    Args:
        form_data: OAuth2PasswordRequestForm containing username (email) and password
        session: Database session
    
    Returns:
        Dictionary with access_token and token_type
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # OAuth2PasswordRequestForm uses "username" field, but we use email
    user = crud.get_user_by_email(session, form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user data
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}

