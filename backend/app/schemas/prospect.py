"""
Pydantic schemas for Prospect API validation.
"""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from app.models import ProspectSource, ProspectStatus

class ProspectBase(BaseModel):
    """Base schema with common fields."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    company_size: Optional[str] = Field(None, max_length=50)
    market: Optional[str] = Field(None, max_length=100)
    source: ProspectSource
    source_notes: Optional[str] = None

class ProspectCreate(ProspectBase):
    """Schema for creating a new prospect."""
    product_interest_ids: Optional[List[int]] = Field(
        default=[],
        description="List of product IDs the prospect is interested in"
    )

class ProspectUpdate(BaseModel):
    """Schema for updating an existing prospect."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    company_size: Optional[str] = Field(None, max_length=50)
    market: Optional[str] = Field(None, max_length=100)
    source: Optional[ProspectSource] = None
    source_notes: Optional[str] = None
    status: Optional[ProspectStatus] = None

class ProspectProductLink(BaseModel):
    """Schema for linking a prospect to a product."""
    product_id: int
    notes: Optional[str] = None

class Prospect(ProspectBase):
    """Schema for prospect response (includes DB fields)."""
    id: int
    status: ProspectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attribute = True