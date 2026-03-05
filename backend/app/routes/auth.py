"""
Authentication routes.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.auth import (
  authenticate_user,
  create_access_token,
  get_password_hash,
)
from app.schemas.auth import UserRegister, Token, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
  """Register a new user. """
  # Check if user already exists
  existing_user = db.query(User).filter(User.email == user_data.email).first()
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Email already registered"
    )

  # Create new user
  hashed_password = get_password_hash(user_data.password)
  new_user = User(
    email=user_data.email,
    hashed_password=hashed_password,
    fisrt_name=user_data.first_name,
    last_name=user_data.last_name,
    is_active=True,
  )

  db.add(new_user)
  db.commit()
  db.refresh(new_user)

  return new_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
       raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Incorrect email or password",
          headers={"WWW-Authenticate": "Bearer"},
       )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
   """Get current authenticated user."""
   return current_user

