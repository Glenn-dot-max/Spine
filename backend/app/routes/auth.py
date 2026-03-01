"""
Authentication routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, User as UserSchema, Token
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  """
  Register a new user.

  - **email**: Valid email address (unique)
  - **password**: Strong password (min 8 chars, includes letters and numbers)
  - **first_name**: Optional
  - **last_name**: Optional
  """
  # Check if user already exists
  existing_user = db.query(User).filter(User.email == user_data.email).first()

  if existing_user:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email already registered"
    )
  
  # Create new user
  db_user = User(
      email=user_data.email,
      hashed_password=hash_password(user_data.password),
      first_name=user_data.first_name,
      last_name=user_data.last_name,
      is_active=True,
      is_superuser=False
  )

  db.add(db_user)
  db.commit()
  db.refresh(db_user)

  return db_user

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
  """
  Login with email and password.
  
  Returns JWT access and refresh tokens.
  """
  # Find user by email
  user = db.query(User).filter(User.email == credentials.email).first()

  if not user:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
  
  # Verify password
  if not verify_password(credentials.password, user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
  
  # Check if user is active
  if not user.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User account is inactive",
    )
  
  # Create JWT tokens
  access_token = create_access_token(
      data={"sub": user.email},
      expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  )

  refresh_token = create_refresh_token(
      data={"sub": user.email},
      expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
  )

  return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer"
  }

@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user)):
  """
  Get current authenticated user's information.

  Requires authentification (Bearer token).
  """
  return current_user
