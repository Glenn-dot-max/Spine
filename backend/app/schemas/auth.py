"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
  """Base user schema."""
  email: EmailStr
  first_name: Optional[str] = None
  last_name: Optional[str] = None

class UserCreate(UserBase):
  """Schema for user registration."""
  password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

class UserLogin(BaseModel):
  """Schema for user login."""
  email: EmailStr
  password: str

class User(UserBase):
  """Schema for user response."""
  id: int
  is_active: bool
  is_superuser: bool
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True

class Token(BaseModel):
  """Schema for JWT token response."""
  access_token: str
  refresh_token: str
  token_type: str = "bearer"

class TokenPayload(BaseModel):
  """Schema for JWT token payload."""
  sub: str  # User email
  exp: int  # Expiration time
  type: str  # Token type (access or refresh)
  