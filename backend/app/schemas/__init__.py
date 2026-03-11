"""
Pydantic schemas for Spine CRM.
"""
from .product import Product, ProductCreate, ProductUpdate
from .prospect import Prospect, ProspectCreate, ProspectUpdate
from .prospect_product import ProspectProductLink, ProspectProductResponse
from .auth import UserRegister, UserLogin, Token, UserResponse

__all__ = [
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "Prospect",
    "ProspectCreate",
    "ProspectUpdate",
    "ProspectProductLink",
    "ProspectProductResponse",
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "Token",
]

from typing import List
from pydantic import BaseModel

class ProductImportPreview(BaseModel):
    """Preview of Excel/CSV before importing."""
    sample_data: List[dict]
    total_rows: int
    columns_detected: List[str]
    warnings: List[str]

class ProductImportResult(BaseModel):
    """Result of import operation."""
    total_rows: int
    created: int
    updated: int
    skipped: int
    errors: List[dict]