"""
Pydantic schemas for Spine CRM.
"""
from .product import Product, ProductCreate, ProductUpdate
from .prospect import Prospect, ProspectCreate, ProspectUpdate
from .prospect_product import ProspectProductLink
from .auth import User, UserCreate, UserLogin, Token, TokenPayload

__all__ = [
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "Prospect",
    "ProspectCreate",
    "ProspectUpdate",
    "ProspectProductLink",
    "User",
    "UserCreate",
    "UserLogin",
    "Token",
    "TokenPayload",
]