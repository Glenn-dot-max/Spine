"""
Pydantic schemas for Campaign API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

# ==================== CAMPAIGN =====================

class CampaignBase(BaseModel):
    """Base schema for campaign data."""
    name: str = Field(..., min_length=1, max_length=255, description="Trade show name")
    event_date: date = Field(..., description="Date of the trade show")
    end_date: Optional[date] = Field(None, description="End date of the trade")
    location: Optional[str] = Field(None, max_length=255, description="Location of the trade show")
    distributor_name: Optional[str] = Field(None, max_length=255, description="Name of the distributor (for salon distributeur)")
    description: Optional[str] = Field(None, description="General notes about trade show")
    status: Optional[str] = Field("upcoming", description="Status: upcoming, active, completed, archived")

class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    pass

class CampaignUpdate(BaseModel):
    """Schema for updating campaign details."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    event_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    distributor_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None

class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    # Stats
    contact_count: Optional[int] = 0
    product_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ==================== CAMPAIGN CONTACTS =====================

class CampaignContactAdd(BaseModel):
    """Schema for adding a prospect to a campaign."""
    prospect_id: int
    status: Optional[str] = Field("pending", description="Status of the contact in the campaign")
    notes: Optional[str] = Field(None, description="Notes about the contact in the campaign")

class CampaignContactBulkAdd(BaseModel):
    """Schema for adding multiple prospects to a campaign."""
    prospect_ids: List[int]
    status: Optional[str] = Field("pending", description="Status of the contacts in the campaign")

class CampaignContactUpdate(BaseModel):
    """Schema for updating a campaign contact."""
    status: Optional[str] = None
    notes: Optional[str] = None

class CampaignContactResponse(BaseModel):
    """Schema for campaign contact response."""
    id: int
    campaign_id: int
    prospect_id: int
    status: str
    notes: Optional[str]
    added_at: datetime

    prospect_email: Optional[str] = None
    prospect_first_name: Optional[str] = None
    prospect_last_name: Optional[str] = None
    prospect_company: Optional[str] = None

    class Config:
        from_attributes = True

# ==================== CAMPAIGN PRODUCTS =====================
class CampaignProductAdd(BaseModel):
    """Schema for adding a product to a campaign."""
    product_id: int

class CampaignProductBulkAdd(BaseModel):
    """Schema for adding multiple products to a campaign."""
    product_ids: List[int]

class CampaignProductResponse(BaseModel):
    """Schema for campaign product response."""
    id: int
    campaign_id: int
    product_id: int
    added_at: datetime

    product_item_number: Optional[str] = None
    product_name: Optional[str] = None
    product_categories: Optional[str] = None

    class Config:
        from_attributes = True

# ==================== CAMPAIGN STATS =====================
class CampaignStats(BaseModel):
    """Schema for campaign statistics."""
    total_contacts: int
    contacts_by_status: dict
    total_products: int