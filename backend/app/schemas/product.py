"""
Pydantic schemas for Product API validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    """Base schema with common fields."""
    item_number: str = Field(..., min_length=1, max_length=100, description="Product SKU/item code")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    short_description: Optional[str] = Field(None, description="Brief product description")

class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass

class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""
    item_number: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    short_description: Optional[str] = None
  
class Product(ProductBase):
    """Schema for productresponse (includes DB fields)."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attribute = True
