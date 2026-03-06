"""
API routes for Spine CRM.
"""
from .products import router as products_router
from .prospects import router as prospects_router
from .prospect_products import router as prospect_products_router
from .auth import router as auth_router

__all__ = [
    "products_router", 
    "prospects_router", 
    "prospect_products_router",
    "auth_router"
]