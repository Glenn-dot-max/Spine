"""
Pydantic schemas for Campaign API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

# ==================== CAMPAIGN =====================

class CampaignBase(BaseModel):
    """Base schema for campaign data."""
    name: str = Field(..., min_length=1, max_length=255)
    event_date: date
    end_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    distributor_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field("upcoming")

    followup_delay_1: Optional[int] = Field(7, ge=1, description="Delay in days for first follow-up email")
    followup_delay_2: Optional[int] = Field(14, ge=1, description="Delay in days for second follow-up email")
    followup_delay_3: Optional[int] = Field(21, ge=1, description="Delay in days for third follow-up email")

    template_initial_id: Optional[int] = None
    template_followup_1_id: Optional[int] = None
    template_followup_2_id: Optional[int] = None
    template_followup_3_id: Optional[int] = None
    
class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    event_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    distributor_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None

    followup_delay_1: Optional[int] = Field(None, ge=1)
    followup_delay_2: Optional[int] = Field(None, ge=1)
    followup_delay_3: Optional[int] = Field(None, ge=1)

class CampaignResponse(CampaignBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    followup_delay_1: int
    followup_delay_2: int
    followup_delay_3: int

    contact_count: Optional[int] = 0
    product_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ==================== CAMPAIGN CONTACTS =====================
class CampaignContactAdd(BaseModel):
    prospect_id: int
    status: Optional[str] = Field("pending")
    notes: Optional[str] = None

class CampaignContactBulkAdd(BaseModel):
    prospect_ids: List[int]
    status: Optional[str] = Field("pending")

class CampaignContactUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

    custom_followup_delay_1: Optional[int] = Field(None, ge=1)
    custom_followup_delay_2: Optional[int] = Field(None, ge=1)
    custom_followup_delay_3: Optional[int] = Field(None, ge=1)

class CampaignContactResponse(BaseModel):
    id: int
    campaign_id: int
    prospect_id: int
    status: str
    notes: Optional[str]
    added_at: datetime

    email_sequence_step: Optional[int] = 0
    next_follow_up_scheduled_at: Optional[datetime] = None

    custom_followup_delay_1: Optional[int] = None
    custom_followup_delay_2: Optional[int] = None
    custom_followup_delay_3: Optional[int] = None

    prospect_email: Optional[str] = None
    prospect_first_name: Optional[str] = None
    prospect_last_name: Optional[str] = None
    prospect_company: Optional[str] = None

    class Config:
        from_attributes = True

# ==================== CAMPAIGN PRODUCTS =====================
class CampaignProductAdd(BaseModel):
    product_id: int

class CampaignProductBulkAdd(BaseModel):
    product_ids: List[int]

class CampaignProductResponse(BaseModel):
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
    total_contacts: int
    contacts_by_status: dict
    total_products: int
