"""
API routes for Email Templates CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models.user import User
from app.models.email_template import EmailTemplate
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    EmailTemplatePreviewRequest,
    EmailTemplatePreviewResponse
)
from app.api.deps import get_current_user
from app.services.email.template_renderer import advanced_renderer

router = APIRouter(prefix="/templates", tags=["email_templates"])

# ============== LIST TEMPLATES ==============
@router.get("", response_model=List[EmailTemplateResponse])
def list_templates(
    category: Optional[str] = None,
    include_global: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    """
    List all templates for the current user.
    
    - User's own templates
    - Global templates (if include_global=True)
    """
    query = db.query(EmailTemplate)

    if category:
        query = query.filter(EmailTemplate.category == category)

    if include_global:
        query = query.filter(
            (EmailTemplate.user_id) 
        )
