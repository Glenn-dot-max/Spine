"""
Pydantic schemas for prospect-product relationships.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProspectProductLink(BaseModel):
    """Schema for linking prospect to product."""
    product_id: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ProspectProductResponse(BaseModel):
    """Schema for prospect-product relationship response."""
    id: int
    prospect_id: int
    product_id: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True