"""
API routes for Spine CRM.
"""
from .products import router as products_router
from .prospects import router as prospects_router

__all__ = ["products_router", "prospects_router"]