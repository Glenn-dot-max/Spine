"""
API routes for Spine CRM.
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .products import router as products_router
from .prospects import router as prospects_router
from .prospect_products import router as prospect_products_router
from .product_import import router as product_import_router
from .prospect_import import router as prospect_import_router
from .campaign_emails import router as campaign_emails_router
from .email_responses import router as email_responses_router
from .followups import router as followups_router

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router, prefix="/api/auth", tags=["auth"])  
api_router.include_router(product_import_router) 
api_router.include_router(prospect_import_router) 
api_router.include_router(products_router)         
api_router.include_router(prospects_router)
api_router.include_router(prospect_products_router)
api_router.include_router(campaign_emails_router, prefix="/api")
api_router.include_router(email_responses_router, prefix="/api")
api_router.include_router(followups_router, prefix="/api")