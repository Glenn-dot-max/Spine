"""
Manual follow-up scheduling endpoint.
User chooses when to schedule follow-ups.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from app.db import get_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect
from app.api.deps import get_current_user
from app.services.email.email_service import EmailService
from app.services.followup_utils import get_effective_delay, schedule_next_followup

router = APIRouter(prefix="/campaigns", tags=["follow-ups"])

# ================= SCHEMAS =================

class ScheduleFollowUpRequest(BaseModel):
    scheduled_at: datetime

class UpdateContactDelayRequest(BaseModel):
    custom_followup_delay_1: Optional[int] = None
    custom_followup_delay_2: Optional[int] = None
    custom_followup_delay_3: Optional[int] = None

# ================= VOIR LES FOLLOW-UPS PLANIFIÉS =================

@router.get("/{campaign_id}/followups/scheduled")
def get_scheduled_followups(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne tous les follow-ups planifiés pour une campagne.
    Inclut les délais effectifs (custom ou campagne)
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
    
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.next_follow_up_scheduled_at.isnot(None),
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
                "last_sent": contact.last_email_sent_at.isoformat() if contact.last_email_sent_at else None,
                "scheduled_at": contact.next_follow_up_scheduled_at.isoformat(),
                "is_due": contact.next_follow_up_scheduled_at <= datetime.utcnow(),
                "effective_delay_1": contact.custom_followup_delay_1 or campaign.followup_delay_1,
                "effective_delay_2": contact.custom_followup_delay_2 or campaign.followup_delay_2,
                "effective_delay_3": contact.custom_followup_delay_3 or campaign.followup_delay_3,
            })

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "scheduled_delays": {
            "delay_1": campaign.followup_delay_1,
            "delay_2": campaign.followup_delay_2,
            "delay_3": campaign.followup_delay_3,
        },
        "total_scheduled": len(scheduled),
        "scheduled_followups": scheduled
    }

# ================= PLANIFIER UN FOLLOW-UP MANUELLEMENT =================
@router.post("/{campaign_id}/contacts/{prospect_id}/schedule-followup")
def schedule_followup(
    campaign_id: int, 
    prospect_id: int,
    scheduled_at: datetime = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Planifie manuellement un follow-up à une date précise.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact for prospect {prospect_id} in campaign {campaign_id} not found")
    
    if not contact.last_email_sent_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot schedule follow-up for a contact that has not received any email yet")
    
    if contact.status == "responded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot schedule follow-up for a contact that has already responded")
    
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()

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
    days_from_now: int = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Planifie le prochian follow-up automatiquement selon les délais de la campagne/contact.
    Si days_from_now est fourni, utilise ce délai. Sinon utilise les délais configurés (custom ou campagne).
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact for prospect {prospect_id} in campaign {campaign_id} not found")
    
    if days_from_now is not None:
        suggested_date = datetime.utcnow() + timedelta(days=days_from_now)
    else:
        delay = get_effective_delay(contact, campaign, contact.email_sequence_step + 1)
        if delay is None:
            return {
                "message": "No more follow-ups to schedule for this contact",
                "current_step": contact.email_sequence_step
            }
        suggested_date = datetime.utcnow() + timedelta(days=delay)

    return schedule_followup(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        scheduled_at=suggested_date,
        db=db,
        current_user=current_user
    )

# ================= METTRE À JOUR LES DÉLAIS DE SUIVI PERSONNALISÉS =================
@router.put("/{campaign_id}/contacts/{prospect_id}/followup-delays")
def update_contact_followup_delays(
    campaign_id: int,
    prospect_id: int,
    delays: UpdateContactDelayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour les délais de suivi personnalisés pour un contact.
    L'utilisateur peut définir des délais spécifiques pour chaque étape de suivi.
    Mettre null permet de revenir au délai de la campagne.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact for prospect {prospect_id} in campaign {campaign_id} not found")
    
    if delays.custom_followup_delay_1 is not None:
        contact.custom_followup_delay_1 = delays.custom_followup_delay_1
    if delays.custom_followup_delay_2 is not None:
        contact.custom_followup_delay_2 = delays.custom_followup_delay_2
    if delays.custom_followup_delay_3 is not None:
        contact.custom_followup_delay_3 = delays.custom_followup_delay_3

    db.commit()

    return {
        "prospect_id": prospect_id,
        "custom_delays": {
            "delay_1": contact.custom_followup_delay_1,
            "delay_2": contact.custom_followup_delay_2,
            "delay_3": contact.custom_followup_delay_3,
        },
        "effective_delays": {
            "delay_1": contact.custom_followup_delay_1 or campaign.followup_delay_1,
            "delay_2": contact.custom_followup_delay_2 or campaign.followup_delay_2,
            "delay_3": contact.custom_followup_delay_3 or campaign.followup_delay_3,
        },
        "message": "Custom follow-up delays updated successfully"
    }

# ================= ENVOYER LES FOLLOW-UPS DUS =================
@router.post("/{campaign_id}/followups/send-due")
def send_due_followups(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envoie tous les follow-ups qui sont dus.
    Après chaque envoie, planifie automatiquement le prochain follow-up selon les délais configurés (custom ou campagne).
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    if not current_user.has_email_configured:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not have email configured")
    
    now = datetime.utcnow()
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.next_follow_up_scheduled_at.isnot(None),
        CampaignContact.next_follow_up_scheduled_at <= now,
        CampaignContact.status == "contacted"
    ).all()

    if not contacts:
        return {"due_contacts": 0, "message": "No follow-ups are due at this time"}
    
    email_service = EmailService(db)
    sent = 0
    failed = 0
    errors = []
    next_followups = []

    for contact in contacts:
        try:
            prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
            if not prospect:
                failed += 1
                continue

            email_service.send_campaign_email(
                campaign=campaign,
                contact=contact,
                prospect=prospect,
                user=current_user
            )

            next_date = schedule_next_followup(contact, campaign)
            sent += 1

            if next_date:
                next_followups.append({
                    "prospect_id": prospect.id,
                    "next_followup_at": next_date.isoformat()
                })

        except Exception as e:
            failed += 1
            errors.append({"prospect_id": contact.prospect_id, "error": str(e)})

    db.commit()

    return {
        "due_contacts": len(contacts),
        "sent": sent,
        "failed": failed,
        "errors": errors,
        "next_followups_scheduled": next_followups,
        "message": f"{sent} follow-ups sent, {failed} failed"
    }

# ================= SUPPRIMER UN FOLLOW-UP PLANIFIÉ =================
@router.post("/{campaign_id}/contacts/{prospect_id}/followup")
def cancel_followup(
    campaign_id: int,
    prospect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Annule un follow-up planifié en supprimant la date de suivi du contact.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact for prospect {prospect_id} in campaign {campaign_id} not found")
    
    contact.next_follow_up_scheduled_at = None
    db.commit()

    return {"prospect_id": prospect_id, "message": "Follow-up cancelled successfully"}