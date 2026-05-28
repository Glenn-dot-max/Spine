"""
Email response detection endpoints.
Checks for replies from prospects and updates their status.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.db import get_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect, ProspectStatus
from app.api.deps import get_current_user
from app.services.email.gmail_response_checker import check_gmail_thread_for_response
from app.services.email.outlook_response_checker import check_outlook_conversation_for_response

router = APIRouter(prefix="/campaigns", tags=["email-responses"])


@router.post("/{campaign_id}/contacts/{prospect_id}/check-response")
def check_contact_response(
    campaign_id: int,
    prospect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a specific campaign contact has responded to an email.
    Updates status to 'responded' if a reply is detected.
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
    
    # Get campaign contact
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not linked to campaign {campaign_id}"
        )
    
    # Check if email was sent
    if not contact.email_thread_id or not contact.last_email_sent_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email has been sent to this prospect yet"
        )
    
    # Already marked as responded? Skip check
    if contact.status == "responded":
        return {
            "already_responded": True,
            "status": "responded",
            "message": "Prospect already marked as responded"
        }
    
    # Get prospect
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    
    # Determine provider to use
    provider = current_user.default_email_provider
    if not provider:
        provider = "gmail" if current_user.gmail_connected else "outlook"
    
    try:
        # Check for responses based on provider
        if provider == "gmail":
            response_data = check_gmail_thread_for_response(
                user=current_user,
                db=db,
                thread_id=contact.email_thread_id,
                prospect_email=prospect.email
            )
        elif provider == "outlook":
            response_data = check_outlook_conversation_for_response(
                user=current_user,
                db=db,
                conversation_id=contact.email_thread_id,
                prospect_email=prospect.email
            )
        else:
            raise Exception(f"Unknown provider: {provider}")
        
        # If response found, update status
        if response_data["has_response"]:
            contact.status = "responded"
            contact.response_received_at = datetime.utcnow()
            contact.last_response_content = response_data.get("response_content", "")[:1000]  # Store first 1000 chars
            db.commit()
            
            return {
                "has_response": True,
                "status": "responded",
                "response_date": contact.response_received_at,
                "response_preview": response_data.get("response_content", "")[:200]
            }
        else:
            return {
                "has_response": False,
                "status": contact.status,
                "message": "No response detected yet"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check for response: {str(e)}"
        )


@router.post("/{campaign_id}/check-all-responses")
def check_all_campaign_responses(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check all campaign contacts for responses.
    Useful for batch checking.
    """
    # Verify campaign exists
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Get all contacts that have been emailed but not responded
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.email_thread_id.isnot(None),
        CampaignContact.status == "contacted"
    ).all()
    
    if not contacts:
        return {
            "checked": 0,
            "responses_found": 0,
            "message": "No contacts to check"
        }
    
    # Determine provider
    provider = current_user.default_email_provider
    if not provider:
        provider = "gmail" if current_user.gmail_connected else "outlook"
    
    checked = 0
    responses_found = 0
    errors = []
    
    for contact in contacts:
        try:
            # Get prospect
            prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
            if not prospect:
                continue
            
            # Check for response
            if provider == "gmail":
                response_data = check_gmail_thread_for_response(
                    user=current_user,
                    db=db,
                    thread_id=contact.email_thread_id,
                    prospect_email=prospect.email
                )
            elif provider == "outlook":
                response_data = check_outlook_conversation_for_response(
                    user=current_user,
                    db=db,
                    conversation_id=contact.email_thread_id,
                    prospect_email=prospect.email
                )
            else:
                continue
            
            checked += 1
            
            # Update if response found
            if response_data["has_response"]:
                contact.status = "responded"
                contact.response_received_at = datetime.utcnow()
                contact.last_response_content = response_data.get("response_content", "")[:1000]
                responses_found += 1
            
        except Exception as e:
            errors.append({
                "prospect_id": contact.prospect_id,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "checked": checked,
        "responses_found": responses_found,
        "new_responded": responses_found,
        "errors": errors if errors else None
    }

# =============== QUALIFIER UN CONTACT ==================

class QualifyContactRequest(BaseModel):
    """Schéma pour qualifier un contact après réception d'une réponse."""
    qualification: str # "oven", "fridge", "trash", "converted"
    notes: Optional[str] = None
    
VALID_QUALIFICATIONS = {"oven", "fridge", "trash", "converted"}

@router.patch("/{campaign_id}/contacts/{prospect_id}/qualify")
def qualify_contact(
    campaign_id: int,
    prospect_id: int,
    body: QualifyContactRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Qualifie manuellement un contact après réception d'une réponse.
    Met à jour le statut dans CampaignContact et dans Prospect (statut global CRM).

    Qualifications disponibles :
    - "oven" : Intéressé, à suivre activement -> stoppe les follow-ups automatiques
    - "fridge" : Pas maintenant, à recontacter plus tard -> stoppe les follow-ups
    - "trash" : Pas intéressé, ne pas recontacter -> stoppe les follow-ups
    - "converted" : Converti en client -> stoppe les follow-ups et marque prospect comme converti
    """
    if body.qualification not in VALID_QUALIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Qualification invalide. Valeurs acceptées : {VALID_QUALIFICATIONS}"
        )
    
    # Vérifier que la campage appartient à l'utilisateur
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Récupérer le lien campagne-contact
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not linked to campaign {campaign_id}"
        )
    
    # Mettre à jour le statut de la campagne
    contact.status = body.qualification

    # Stopper les follow-ups automatiques pour tous les qualifiés
    contact.next_follow_up_scheduled_at = None

    if body.notes:
        contact.notes = body.notes

    # Mettre à jour le statut global du prospect dans le CRM
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not found"
        )
    
    prospect.status = ProspectStatus(body.qualification)

    db.commit()

    return {
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "campaign_status": contact.status,
        "crm_status": prospect.status if prospect else None,
        "follow_ups_stopped": True,
        "message": f"Contact qualified as {contact.status}. Follow-ups stopped."
    }

