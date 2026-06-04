"""
API routes for campaign email sending.
Separate from campaign CRUD - focuses only on email operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os

ATTACHMENTS_DIR = "/tmp/spine_attachments"

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
from app.services.email_composer import composer
from app.services.email.email_service import EmailService

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
        import traceback
        traceback.print_exc()
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

# ==================== PREVIEW =====================

@router.post("/{campaign_id}/contacts/{prospect_id}/emails/preview", response_model=EmailPreviewResponse)
def preview_email(
    campaign_id: int,
    prospect_id: int,
    step: int = 0,
    overrides: Optional[dict] = Body(None, embed=True, description="Blocs overridés par l'user {greeting, company_intro, catalog_pitch, segment_note, samples, cta, signature, subject}"),
    attachment_names: Optional[List[str]] = Body(None, embed=True, description="Noms des PJ à mentionner dans l'email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview email avant envoi.
    Utilise le composer V1 par blocs conditionnels.
    Accepte des overrides par bloc pour permettre l'édition frontend.
    Retourne les blocs séparément pour édition + le HTML assemblé.
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
        Prospect.id == prospect_id
    ).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not found"
        )

    try:
        result = composer.compose(
            prospect=prospect,
            campaign=campaign,
            sender=current_user,
            db=db,
            step=step,
            overrides=overrides or {},
            attachment_names=attachment_names or [],
        )

        return EmailPreviewResponse(
            subject=result["subject"] or f"Re: {campaign.name}",
            html_body=result["html_body"],
            to_email=prospect.email,
            prospect_name=f"{prospect.first_name} {prospect.last_name}",
            template_used="composer_v1",
            variables_used=result["blocks"],
        )

    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render email preview: {str(e)}"
        )
    
# ===================== PIÈCES JOINTES =====================
@router.post("/{campaign_id}/attachments")
async def upload_campaign_attachments(
    campaign_id: int,
    files: List[UploadFile] = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload PDF attachments for a campaign. 
    Saved to /tpm/spine_attachments/{campaign_id}/
    Max 2 files x 5MB.
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
    
    if len(files) > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 2 attachments allowed"
        )
    
    save_dir = os.path.join(ATTACHMENTS_DIR, str(campaign_id))
    os.makedirs(save_dir, exist_ok=True)

    saved_paths = []
    for f in files:
        content = await f.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {f.filename} exceeds 5MB size limit"
            )
        dest = os.path.join(save_dir, f.filename)
        with open(dest, "wb") as out:
            out.write(content)
        saved_paths.append(dest)

    campaign.attachment_paths = json.dumps(saved_paths)
    db.commit()

    return {"uploaded": [os.path.basename(p) for p in saved_paths]}
