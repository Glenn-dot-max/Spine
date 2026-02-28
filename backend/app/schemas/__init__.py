"""
Pydantic schemas for API validation.
"""
from .product import Product, ProductCreate, ProductUpdate
from .prospect import (
    Prospect,
    ProspectCreate,
    ProspectUpdate,
    ProspectProductLink
)

__all__ = [
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "Prospect",
    "ProspectCreate",
    "ProspectUpdate",
    "ProspectProductLink"
]