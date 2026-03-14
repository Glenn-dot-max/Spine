"""
Manual follow-up scheduling endpoint.
User chooses when to schedule follow-ups.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.db import get_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect
from app.api.deps import get_current_user
from app.services.email.email_service import EmailService

router = APIRouter(prefix="/campaigns", tags=["follow-ups"])

# ================= SCHEMAS =================

class ScheduleFollowUpRequest(BaseModel):
    scheduled_at: datetime  # Date et heure choisies par l'utilisateur pour la relance

class ScheduleFollowUpResponse(BaseModel):
    prospect_id: int
    prospect_name: str
    current_step: int
    scheduled_at: datetime
    message: str


# ================= PLANNIFIER UN FOLLOW-UP =================
@router.post("/{campaign_id}/contacts/{prospect_id}/schedule-followup")
def schedule_followup(
    campaign_id: int,
    prospect_id: int,
    scheduled_at: datetime = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schedule a follow-up email for a specific contact.
    User chooses the exact date/time.
    """
    # Verify campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Get contact
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not linked to campaign {campaign_id}"
        )
    
    # Verify email was sent
    if not contact.last_email_sent_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule follow-up: no initial email sent yet"
        )
    
    # Verify not already responded
    if contact.status == "responded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule follow-up: prospect has already responded"
        )
    
    # Get prospect for response
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()

    # Schedule the follow-up
    contact.next_follow_up_scheduled_at = scheduled_at
    db.commit()

    return {
        "prospect_id": prospect.id,
        "prospect_name": f"{prospect.first_name} {prospect.last_name}",
        "current_step": contact.email_sequence_step,
        "scheduled_at": scheduled_at,
        "message": f"Follow-up scheduled for {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
@router.post("/{campaign_id}/contacts/{prospect_id}/schedule-followup/suggest")
def suggest_followup_date(
    campaign_id: int, 
    prospect_id: int,
    days_from_now: int = Body(3, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Suggest and schedule a follow-up date.
    Quick helper to schedule +X days from now.
    """
    suggested_date = datetime.utcnow() + timedelta(days=days_from_now)

    return schedule_followup(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        scheduled_at=suggested_date,
        db=db,
        current_user=current_user
    )

# ================= VOIR LES FOLLOW-UPS PLANIFIÉS =================
@router.get("/{campaign_id}/followups/scheduled")
def get_scheduled_followups(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    """
    Get all scheduled follow-ups for a campaign.
    """
    # Verify a campaign
    campaign= db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Get contacts with scheduled follow-ups
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.next_follow_up_scheduled_at.isnot(None),
        CampaignContact.status == "contacted"  # Only show those that have been contacted but not responded
    ).order_by(CampaignContact.next_follow_up_scheduled_at).all()

    scheduled = []
    for contact in contacts:
        prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
        if prospect:
            scheduled.append({
                "prospect_id": prospect.id,
                "prospect_name": f"{prospect.first_name} {prospect.last_name}",
                "prospect_email": prospect.email,
                "current_step": contact.email_sequence_step,
                "last_sent": contact.last_email_sent_at.isoformat(),
                "scheduled_at": contact.next_follow_up_scheduled_at.isoformat(),
                "is_due": contact.next_follow_up_scheduled_at <= datetime.utcnow()
            })
    
    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "total_scheduled": len(scheduled),
        "scheduled_followups": scheduled
    }

# ================= ENVOYER LES FOLLOW-UPS DUS =================
@router.post("/{campaign_id}/followups/send-due")
def send_due_followups(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send all follow-ups that are due NOW.
    Only sends contacts where schedules_at <= now.
    """
    # Verify campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Check email configured
    if not current_user.has_email_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must connect GMAIL or OUTLOOK"
        )
    
    # Get contacts with due follow-ups
    now = datetime.utcnow()
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.next_follow_up_scheduled_at.isnot(None),
        CampaignContact.next_follow_up_scheduled_at <= now,
        CampaignContact.status == "contacted" 
    ).all()

    if not contacts:
        return {
            "due_contacts": 0,
            "sent": 0,
            "message": "No follow-ups are due at this time"
        }
    
    # Send follow-ups
    email_service = EmailService(db)
    sent = 0
    failed = 0
    errors = []

    for contact in contacts:
        try:
            # Get prospect
            prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
            if not prospect:
                failed += 1
                continue
            
            # Send follow-up
            result = email_service.send_campaign_email(
                campaign=campaign,
                contact=contact,
                prospect=prospect,
                user=current_user,
            )

            # Clear scheduled date
            contact.next_follow_up_scheduled_at = None
            sent += 1

        except Exception as e:
            failed += 1
            errors.append({
                "prospect_id": contact.prospect_id,
                "error": str(e)
            })

    db.commit()

    return {
        "due_contacts": len(contacts),
        "sent": sent,
        "failed": failed,
        "errors": errors if errors else None,
        "message": f"{sent} follow-ups sent, {failed} failed"
    }

# ================= ANNULER UN FOLLOW-UP PLANIFIÉ =================
@router.post("/{campaign_id}/contacts/{prospect_id}/followup")
def cancel_followup(
    campaign_id: int,
    prospect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a scheduled follow-up.
    """
    # Verify campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Get contact
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not linked to campaign {campaign_id}"
        )
    
    # Cancel
    contact.next_follow_up_scheduled_at = None
    db.commit()

    return {
        "prospect_id": prospect_id,
        "message": "Follow-up cancelled"  
    }
