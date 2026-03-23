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
from app.services.email.advanced_template_renderer import advanced_renderer

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
            (EmailTemplate.user_id == current_user.id) | (EmailTemplate.user_id == None)        )
    else:
        query = query.filter(EmailTemplate.user_id == current_user.id)

    # Order by : user's templates first, then global, then by name
    query = query.order_by(
        EmailTemplate.user_id.desc().nullslast(),
        EmailTemplate.name
    )

    return query.all()

# ============== GET TEMPLATE ==============
@router.get("/{template_id}", response_model=EmailTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Get a specific template by ID. """
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Template {template_id} not found"
        )
    
    # Chech access: user can only access their own templates or global templates
    if template.user_id and template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have access to this template"
        )
    
    return template

# ============== CREATE TEMPLATE ==============
@router.post("", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Create a new email template. """

    # Check if template with same name already exists for the user
    existing = db.query(EmailTemplate).filter(
        EmailTemplate.user_id == current_user.id,
        EmailTemplate.name == template_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Template with name '{template_data.name}' already exists"
        )
    
    # extract variables from templates
    subject_vars = advanced_renderer.extract_variables(template_data.subject_template)
    body_vars = advanced_renderer.extract_variables(template_data.body_template)
    all_vars = list(set(subject_vars + body_vars))

    # Create template
    template = EmailTemplate(
        user_id=current_user.id,
        name=template_data.name,
        category=template_data.category,
        subject_template=template_data.subject_template,
        body_template=template_data.body_template,
        variables={"used_variables": all_vars} if all_vars else None,
        is_active=template_data.is_active,
        is_default=template_data.is_default
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template

# ============== UPDATE TEMPLATE ==============
@router.put("/{template_id}", response_model=EmailTemplateResponse)
def update_template(
    template_id: int,
    template_data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Update an existing email template. """
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Template {template_id} not found"
        )
    
    # Check ownership (can't modify global templates)
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only modify your own templates"
        )
    
    # Update fields
    update_data = template_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(template, field, value)

    # Re-extract variables if templates changed
    if template_data.subject_template or template_data.body_template:
        subject_vars = advanced_renderer.extract_variables(template.subject_template)
        body_vars = advanced_renderer.extract_variables(template.body_template)
        all_vars = list(set(subject_vars + body_vars))
        template.variables = {"used_variables": all_vars} if all_vars else None

    db.commit()
    db.refresh(template)

    return template

# ============== DELETE TEMPLATE ==============
@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Delete an email template. """
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Template {template_id} not found"
        )
    
    # Check ownership (can't delete global templates)
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only delete your own templates"
        )
    
    db.delete(template)
    db.commit()

    return None

# ============== PREVIEW TEMPLATE ==============
@router.post("/{template_id}/preview", response_model=EmailTemplatePreviewResponse)
def preview_template(
    template_id: int,
    preview_data: EmailTemplatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Render a preview of the email template with provided variables. """
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Template {template_id} not found"
        )
    
    # Check access: user can only access their own templates or global templates
    if template.user_id and template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have access to this template"
        )
    
    # Build context from preview data
    context = {}

    if preview_data.prospect_data:
        context['prospect'] = preview_data.prospect_data

    if preview_data.campaign_data:
        context['campaign'] = preview_data.campaign_data

    if preview_data.user_data:
        context['user'] = preview_data.user_data

    if preview_data.custom_data:
        context['custom'] = preview_data.custom_data

    # Add default values if not provided
    if 'prospect' not in context:
        context['prospect'] = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'company_name': 'Example Inc.'
        }

    if 'campaign' not in context:
        context['campaign'] = {
            'name': 'Trade Show 2026',
            'description': 'Convention center'
        }

    if 'user' not in context:
        context['user'] = {
            'first_name': current_user.first_name or 'Sales',
            'last_name': current_user.last_name or 'Rep',        
        }

    # Render templates
    try:
        subject = advanced_renderer.render(template.subject_template, context)
        body = advanced_renderer.render(template.body_template, context)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Error rendering template: {str(e)}"
        )
    
    # Extract which variables were actually used
    variables_used = {}
    for var in advanced_renderer.extract_variables(template.subject_template + template.body_template):
        value = advanced_renderer._get_nested_value(var, context)
        variables_used[var] = str(value) if value else "(not set)"

    return EmailTemplatePreviewResponse(
        subject=subject,
        body=body,
        variables_used=variables_used
    )
