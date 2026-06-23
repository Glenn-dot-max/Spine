"""
Pydantic schemas for Spine CRM.
"""
from .product import Product, ProductCreate, ProductUpdate
from .prospect import Prospect, ProspectCreate, ProspectUpdate
from .prospect_product import ProspectProductLink, ProspectProductResponse
from .auth import UserRegister, UserLogin, Token, UserResponse
from .campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignContactAdd,
    CampaignContactBulkAdd,
    CampaignContactUpdate,
    CampaignContactResponse,
    CampaignProductAdd,
    CampaignProductBulkAdd,
    CampaignProductResponse,
    CampaignStats
)
from .email import (
    EmailSendRequest,
    EmailSendResponse,
    BulkEmailSendRequest,
    BulkEmailSendResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
)
from .company import Company as CompanySchema, CompanyCreate, CompanyUpdate

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
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignResponse",
    "CampaignContactAdd",
    "CampaignContactBulkAdd",
    "CampaignContactUpdate",
    "CampaignContactResponse",
    "CampaignProductAdd",
    "CampaignProductBulkAdd",
    "CampaignProductResponse",
    "CampaignStats",
    # Email schemas
    "EmailSendRequest",
    "EmailSendResponse",
    "BulkEmailSendRequest",
    "BulkEmailSendResponse",
    "EmailPreviewRequest",
    "EmailPreviewResponse",
    "CompanySchema",
    "CompanyCreate",
    "CompanyUpdate",
]

from typing import List
from pydantic import BaseModel

class ProductImportPreview(BaseModel):
    """Preview of Excel/CSV before importing."""
    sample_data: List[dict]
    total_rows: int
    columns_detected: List[str]
    warnings: List[str]

class PDFCreditCheck(BaseModel):
    """Fast pre-check before calling Haiku Vision - no AI call, just page analysis."""
    num_pages: int
    estimated_mode: str
    requires_confirmation: bool
    warning_message: str

class PDFImportPreview(BaseModel):
    """Preview of PDF catalog extraction by Haiku before importing."""
    products: List[dict]
    total_extracted: int
    extraction_mode: str
    warnings: List[str]

class PDFToCatalogResult(BaseModel):
    """Résultat de l'import PDF vers catalogue."""
    catalog_id: int
    catalog_name: str
    products_created: int
    products_skipped: int
    pdf_attached: bool
    
class ProductImportResult(BaseModel):
    """Result of import operation."""
    total_rows: int
    created: int
    updated: int
    skipped: int
    errors: List[dict]