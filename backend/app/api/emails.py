"""
Email sending endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.api.deps import get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/emails", tags=["emails"])


class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    provider: str = None  # "gmail" or "outlook", if None use default


@router.post("/send")
async def send_email(
    email_data: EmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send an email using the configured OAuth provider.
    """
    # TODO: Implement actual email sending logic
    return {
        "status": "success",
        "message": f"Email sent to {email_data.to}",
        "provider": email_data.provider or current_user.default_email_provider
    }