"""
SPINE V1 - Product schemas
==========================
Rôle : Validation Pydantic pour les endpoints produits. 
Dépendances : models/product.py
Utilisé par : routes/products.py, routes/product_import.py
Dernière modification : 2026-05-29 - Ajout champs food distribution
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    item_number: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    formats: Optional[str] = None
    price_range: Optional[str] = None
    certifications: Optional[str] = None
    segments: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    item_number: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    formats: Optional[str] = None
    price_range: Optional[str] = None
    certifications: Optional[str] = None
    segments: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
