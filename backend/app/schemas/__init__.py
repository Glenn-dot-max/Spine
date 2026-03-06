"""
Pydantic schemas for Spine CRM.
"""
from .product import Product, ProductCreate, ProductUpdate
from .prospect import Prospect, ProspectCreate, ProspectUpdate
from .prospect_product import ProspectProductLink
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