"""
SPINE V1 - company schema
========================
Role: Pydantic validation for company API endpoints.
Dependencies: app.models.company
Used by: routes/companies.py
Last modified: 2026-06-21 - chain_level + end_user_type
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.company import ChainLevel, EndUserType

class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    market: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    chain_level: Optional[ChainLevel] = None
    end_user_type: Optional[EndUserType] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    market: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    chain_level: Optional[ChainLevel] = None
    end_user_type: Optional[EndUserType] = None

class Company(CompanyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True