"""
SPINE V1 - prospect schema
===========================
Rôle : Schéma Pydantic pour la validation et la sérialisation des prospects.
Dépendances : app.models (ProspectSource, ProspectStatus, ProspectCanal)
Utilisé par : routes/prospects.py, routes/prospect_import.py
Sécurité : Validation stricte des champs de saisie.
Dernière modification : 2026 - 06 - 03 - ajout canal + canal_detail.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from app.models import ProspectSource, ProspectStatus, ProspectCanal

class ProspectBase(BaseModel):
    """Base schema for prospect with common fields."""
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    company_size: Optional[str] = Field(None, max_length=50)
    market: Optional[str] = Field(None, max_length=100)
    source: ProspectSource
    source_notes: Optional[str] = None

    # Sprint 4 - canal context for campaign personalization
    canal: Optional[ProspectCanal] = None
    canal_detail: Optional[str] = Field(None, max_length=255)

class ProspectCreate(ProspectBase):
    """Schema for creating a new prospect."""
    product_interest_ids: Optional[List[int]] = Field(
        default=[],
        description="List of product IDs the prospect is interested in."
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

    # Sprint 4 - canal context for campaign personalization
    canal: Optional[ProspectCanal] = None
    canal_detail: Optional[str] = Field(None, max_length=255)

class ProspectProductLink(BaseModel):
    """Schema for linking a prospect to a product interest."""
    product_id: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ProspectProductResponse(BaseModel):
    """Schema for prospect-product link response."""
    id: int
    prospect_id: int
    product_id: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Prospect(ProspectBase):
    """Schema for prospect response (includes DB fields)."""
    id: int
    status: ProspectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True