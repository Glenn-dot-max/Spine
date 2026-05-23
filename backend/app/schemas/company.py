"""
Pydantic schemas for Company API validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.company import StructureType, ContactType


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    market: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    type_structure: Optional[StructureType] = None
    type_contact: Optional[ContactType] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    market: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    type_structure: Optional[StructureType] = None
    type_contact: Optional[ContactType] = None


class Company(CompanyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True