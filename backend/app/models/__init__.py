"""
SQLAlchemy models for Spine CRM.
"""
from .base import Base
from .user import User
from .product import Product
from .prospect import Prospect, ProspectSource, ProspectStatus
from .prospect_product import ProspectProduct
from .campaign import Campaign, CampaignContact, CampaignProduct
from .email_template import EmailTemplate
from .company import Company, StructureType, ContactType
from .oauth_state import OAuthState

__all__ = [
    "Base",
    "User",
    "Product",
    "Prospect",
    "ProspectSource",
    "ProspectStatus",
    "ProspectProduct",
    "Campaign",             
    "CampaignContact",      
    "CampaignProduct",
    "EmailTemplate",
    "Company",
    "StructureType",
    "ContactType",
    "OAuthState",
]