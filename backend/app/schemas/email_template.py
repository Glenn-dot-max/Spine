"""
Pydantic schemas for Email Templates.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class EmailTemplateBase(BaseModel):
    """Base schema for email template."""
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    subject_template: str = Field(..., min_length=1, max_length=500)
    body_template: str = Field(..., min_length=1)
    variables: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_default: bool = False


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating a new template."""
    pass


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an existing template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    subject_template: Optional[str] = Field(None, min_length=1, max_length=500)
    body_template: Optional[str] = Field(None, min_length=1)
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    """Schema for template response."""
    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailTemplatePreviewRequest(BaseModel):
    """Schema for template preview request."""
    prospect_data: Optional[Dict[str, Any]] = None
    campaign_data: Optional[Dict[str, Any]] = None
    user_data: Optional[Dict[str, Any]] = None
    custom_data: Optional[Dict[str, Any]] = None


class EmailTemplatePreviewResponse(BaseModel):
    """Schema for template preview response."""
    subject: str
    body: str
    variables_used: Dict[str, str]