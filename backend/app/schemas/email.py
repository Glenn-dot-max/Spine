"""
Pydantic schemas for email operations.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class EmailSendRequest(BaseModel):
    """Request to send email to specific contact."""
    prospect_id: int = Field(..., description="ID of the prospect to send email to")
    template_override: Optional[str] = Field(None, description="Optional: override template (e.g., 'initial.html')")


class EmailSendResponse(BaseModel):
    """Response after sending a single email."""
    success: bool
    prospect_id: int
    prospect_email: str
    message_id: str
    thread_id: str
    provider: str  # "gmail" or "outlook"
    sequence_step: int
    sent_at: datetime
    
    class Config:
        from_attributes = True


class BulkEmailSendRequest(BaseModel):
    """Request to send emails to multiple contacts."""
    contact_ids: Optional[List[int]] = Field(None, description="Specific contact IDs to send to (optional)")
    status_filter: Optional[str] = Field(None, description="Send to contacts with specific status (e.g., 'pending')")
    template_override: Optional[str] = Field(None, description="Optional: override template")


class BulkEmailSendResponse(BaseModel):
    """Response after sending bulk emails."""
    total: int
    sent: int
    failed: int
    errors: List[dict]
    sent_contacts: List[dict]  # List of successfully sent emails with details


class EmailPreviewRequest(BaseModel):
    """Request to preview email before sending."""
    prospect_id: int
    template_name: Optional[str] = Field(None, description="Template to preview (e.g., 'initial.html')")


class EmailPreviewResponse(BaseModel):
    """Preview of rendered email."""
    subject: str
    html_body: str
    to_email: str
    prospect_name: str
    template_used: str
    variables_used: dict