"""
API routes for campaign email sending.
Separate from campaign CRUD - focuses only on email operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect
from app.schemas.email import (
    EmailSendResponse,
    BulkEmailSendResponse,
    EmailPreviewResponse,
)
from app.api.deps import get_current_user
from app.services.email.email_service import EmailService
from app.services.email.template_renderer import email_renderer

router = APIRouter(prefix="/campaigns", tags=["campaign-emails"])


# ==================== ENVOI INDIVIDUEL =====================

@router.post("/{campaign_id}/contacts/{prospect_id}/emails/send", response_model=EmailSendResponse)
def send_email_to_contact(
    campaign_id: int,
    prospect_id: int,
    template_override: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send email to a specific campaign contact.
    """
    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Get campaign contact link
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} is not linked to campaign {campaign_id}"
        )
    
    # Get prospect data
    prospect = db.query(Prospect).filter(
        Prospect.id == prospect_id,
        Prospect.user_id == current_user.id
    ).first()
    
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not found"
        )
    
    # Check user has email configured
    if not current_user.has_email_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must connect Gmail or Outlook before sending emails"
        )
    
    # Send the email
    email_service = EmailService(db)
    
    try:
        result = email_service.send_campaign_email(
            campaign=campaign,
            contact=contact,
            prospect=prospect,
            user=current_user,
            template_override=template_override
        )
        
        return EmailSendResponse(
            success=result["success"],
            prospect_id=prospect.id,
            prospect_email=result["sent_to"],
            message_id=result["message_id"],
            thread_id=result["thread_id"],
            provider=result["provider"],
            sequence_step=result["sequence_step"],
            sent_at=contact.last_email_sent_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


# ==================== ENVOI EN MASSE =====================

@router.post("/{campaign_id}/emails/send-bulk", response_model=BulkEmailSendResponse)
def send_bulk_emails(
    campaign_id: int,
    contact_ids: Optional[List[int]] = Body(None),
    status_filter: Optional[str] = Body(None),
    template_override: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send emails to multiple campaign contacts in bulk.
    """
    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Check user has email configured
    if not current_user.has_email_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must connect Gmail or Outlook before sending emails"
        )
    
    # Build query for contacts to send to
    query = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    )
    
    # Filter by specific contact IDs
    if contact_ids:
        query = query.filter(CampaignContact.prospect_id.in_(contact_ids))
    
    # Filter by status
    if status_filter:
        query = query.filter(CampaignContact.status == status_filter)
    
    contacts = query.all()
    
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No contacts found matching the criteria"
        )
    
    # Send emails
    email_service = EmailService(db)
    
    try:
        result = email_service.send_bulk_campaign_emails(
            campaign=campaign,
            contacts=contacts,
            user=current_user
        )
        
        # Build detailed response with sent contacts
        sent_contacts = []
        for contact in contacts:
            prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
            if prospect and contact.last_email_sent_at:
                sent_contacts.append({
                    "prospect_id": prospect.id,
                    "email": prospect.email,
                    "name": f"{prospect.first_name} {prospect.last_name}",
                    "sequence_step": contact.email_sequence_step,
                    "sent_at": contact.last_email_sent_at.isoformat()
                })
        
        return BulkEmailSendResponse(
            total=result["total"],
            sent=result["sent"],
            failed=result["failed"],
            errors=result["errors"],
            sent_contacts=sent_contacts
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk emails: {str(e)}"
        )


# ==================== RACCOURCIS PRATIQUES =====================

@router.post("/{campaign_id}/emails/send-initial", response_model=BulkEmailSendResponse)
def send_initial_emails(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send initial emails to all pending contacts.
    """
    return send_bulk_emails(
        campaign_id=campaign_id,
        contact_ids=None,
        status_filter="pending",
        template_override=None,
        db=db,
        current_user=current_user
    )


@router.post("/{campaign_id}/emails/send-followup", response_model=BulkEmailSendResponse)
def send_followup_emails(
    campaign_id: int,
    status_filter: Optional[str] = Body("contacted"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send follow-up emails to contacted prospects.
    """
    return send_bulk_emails(
        campaign_id=campaign_id,
        contact_ids=None,
        status_filter=status_filter,
        template_override=None,
        db=db,
        current_user=current_user
    )


# ==================== PREVIEW (POUR TESTER) =====================

@router.get("/{campaign_id}/contacts/{prospect_id}/emails/preview", response_model=EmailPreviewResponse)
def preview_email(
    campaign_id: int,
    prospect_id: int,
    template_name: Optional[str] = None,
    step: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview email before sending - utilise le même moteur que l'envoi réel.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} is not linked to campaign {campaign_id}"
        )
    
    prospect = db.query(Prospect).filter(
        Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not found"
        )
    
    try:
        email_service = EmailService(db)

        effective_step = step if step is not None else contact.email_sequence_step

        t_name = template_name or email_service._get_template_name(effective_step)
        template = email_service._load_template(current_user, t_name)
        context = email_service._build_context(prospect, campaign, current_user)

        if template:
            from app.services.email.advanced_template_renderer import advanced_renderer
            subject = advanced_renderer.render(template.subject_template, context)
            html_body = advanced_renderer.render(template.body_template, context)
        else:
            subject = email_service._get_fallback_subject(campaign.name, effective_step)
            html_body = email_service._get_fallback_body(
                prospect.first_name,
                campaign.name,
                campaign.location or "our event",
                current_user.first_name or "Sales",
                current_user.last_name or "Team",
                effective_step
            )
        
        return EmailPreviewResponse(
            subject=subject,
            html_body=html_body,
            to_email=prospect.email,
            prospect_name=f"{prospect.first_name} {prospect.last_name}",
            template_used=t_name,
            variables_used={
                "first_name": prospect.first_name,
                "last_name": prospect.last_name,
                "campaign_name": campaign.name,
                "campaign_location": campaign.location,
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render email preview: {str(e)}"
        )