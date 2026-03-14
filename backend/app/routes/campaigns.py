"""
API routes for campaign (trade show) management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models.user import User
from app.models.campaign import Campaign, TradeShowStatus
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# ==================== CRUD DE BASE =====================

@router.get("/", response_model=List[CampaignResponse])
def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all campaigns (trade shows) for the current user.

    Query params:
    - skip: number of records to skip (for pagination)
    - limit: max number of results (max 100)
    - status_filter: filter by status (upcoming, active, completed, archived)

    Returns:
    - List of campaigns with basic info
    """
    query = db.query(Campaign).filter(Campaign.user_id == current_user.id)

    # Optional status filter
    if status_filter:
        try:
            # Validate that the status exists in the enum
            status_enum = TradeShowStatus(status_filter.lower())
            query = query.filter(Campaign.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in TradeShowStatus]}"
            )
        
    # Sort by event date
    query = query.order_by(Campaign.event_date.desc())

    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new campaign (trade show).

    Body:
    {
        "name": "Show Chefs LA 2026",
        "event_date": "2026-01-15",
        "end_date": "2026-01-20",
        "location": "Los Angeles Convention Center",
        "distributor_name": "US Foods",
        "description": "Notes about the show",
        "status": "upcoming"
    }

    Returns:
    - Created campaign with its ID
    """
    # Create the campaign object
    new_campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        event_date=campaign_data.event_date,
        end_date=campaign_data.end_date,
        location=campaign_data.location,
        distributor_name=campaign_data.distributor_name,
        description=campaign_data.description,
        status=campaign_data.status or TradeShowStatus.UPCOMING
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    return new_campaign

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific campaign by ID.

    Path params:
    - campaign_id: ID of the campaign to retrieve

    Returns:
    - Campaign details
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")

    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing campaign.

    Peth params:
    - campaign_id: Campaign ID

    Body (all fiels optional):
   {
        "name":"New Name",
        "location":"New Location",
        "status":"active"
        ...
   } 

   Returns:
   - Updated campaign details
    """

    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Update only provided fields
    update_data = campaign_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)

    return campaign

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a campaign by ID.

    Path params:
    - campaign_id: ID of the campaign to delete

    Returns:
    - 204 No Content on success
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")

    db.delete(campaign)
    db.commit()

    return None  # 204 No Content
  

# ==================== CONTACTS MANAGEMENT =====================

@router.get("/{campaign_id}/contacts", response_model=List[dict])
def list_campaign_contacts(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all contacts (prospects) linked to campaign.
    
    Path params:
    - campaign_id: ID of the campaign

    Returns:
    - List of contacts with prospect details, status, and email sequence info
    """
    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # get all contacts with prospect data
    from app.models.campaign import CampaignContact
    from app.models.prospect import Prospect

    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    ).all()

    # Build response with prospect details
    result = []
    for contact in contacts:
        prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
        if prospect:
            result.append({
                "prospect_id": prospect.id,
                "first_name": prospect.first_name,
                "last_name": prospect.last_name,
                "email": prospect.email,
                "phone_number": prospect.phone_number,
                "company_name": prospect.company_name,
                "position": prospect.position,
                "status": contact.status,
                "notes": contact.notes,
                "email_sequence_step": contact.email_sequence_step,
                "last_email_sent_at": contact.last_email_sent_at,
                "added_at": contact.added_at
            })
    return result


@router.post("/{campaign_id}/contacts", status_code=status.HTTP_201_CREATED)
def add_contact_to_campaign(
    campaign_id: int,
    prospect_id: int, 
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a contact (prospect) to a campaign.

    Path params:
    - campaign_id: ID of the campaign

    Query params:
    - prospect_id: ID of the prospect to add
    - notes: optional notes about this contact in the campaign

    Returns:
    - 201 Created on success
    """
    from app.models.campaign import CampaignContact
    from app.models.prospect import Prospect

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # Check if already linked
    existing = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Prospect {prospect_id} is already linked to campaign {campaign_id}")
    
    # Create link
    contact = CampaignContact(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        notes=notes,
        status="pending",
        email_sequence_step=0
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return {
        "message": "Contact added to successfully",
        "prospect_id": prospect_id,
        "campaign_id": campaign_id
    }

@router.post("/{campaign_id}/contacts/bulk", status_code=status.HTTP_201_CREATED)
def add_campaign_contacts_bulk(
    campaign_id: int,
    prospect_ids: List[int], 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add multiple contacts (prospects) to a campaign in bulk.

    Path params:
    - campaign_id: ID of the campaign

    Body:
    [123, 456, 789]

    Returns:
    - Summary of added/skipped contacts

    """
    from app.models.campaign import CampaignContact
    from app.models.prospect import Prospect

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    added = []
    skipped = []
    not_found = []

    for prospect_id in prospect_ids:
        # Check if already linked
        prospect = db.query(Prospect).filter(
            Prospect.id == prospect_id,
            Prospect.user_id == current_user.id
        ).first()

        if not prospect:
            not_found.append(prospect_id)
            continue

        # Check if already linked
        existing = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.prospect_id == prospect_id
        ).first()

        if existing:
            skipped.append(prospect_id)
            continue

        # Create link
        contact = CampaignContact(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            status="pending",
            email_sequence_step=0
        )

        db.add(contact)
        added.append(prospect_id)

    db.commit()

    return {
        "message": f"Added {len(added)} contacts",
        "added": added,
        "skipped": skipped,
        "not_found": not_found
    }

@router.patch("/{campaign_id}/contacts/{prospect_id}")
def update_campaign_contact(
    campaign_id: int,
    prospect_id: int, 
    status_update: Optional[str] = None,
    notes: Optional[str] = None,
    email_sequence_step: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a contact's status, notes, or email sequence step.

    Path params:
    - campaign_id: ID of the campaign
    - prospect_id: ID of the prospect

    Query params (at least one required):
    - status_update: new status (pending, contacted, interested, not_interested)
    - notes: update notes about this contact
    - email_sequence_step: update the current step in the email sequence

    Returns:
    - Updated contact details
    """
    from app.models.campaign import CampaignContact

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # Get contact link
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect {prospect_id} is not linked to campaign {campaign_id}")
    
    # Update fields if provided
    if status_update is not None:
        contact.status = status_update

    if notes is not None:
        contact.notes = notes

    if email_sequence_step is not None:
        contact.email_sequence_step = email_sequence_step

    db.commit()
    db.refresh(contact)

    return {
        "message": "Contact updated successfully",
        "prospect_id": prospect_id,
        "status": contact.status,
        "notes": contact.notes,
        "email_sequence_step": contact.email_sequence_step
    }

@router.delete("/{campaign_id}/contacts/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact_from_campaign(
    campaign_id: int,
    prospect_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a contact (prospect) from a campaign.

    Path params:
    - campaign_id: ID of the campaign
    - prospect_id: ID of the prospect to remove

    Returns:
    - 204 No Content on success
    """
    from app.models.campaign import CampaignContact

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # Get contact link
    contact = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.prospect_id == prospect_id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect {prospect_id} is not linked to campaign {campaign_id}")
    
    db.delete(contact)
    db.commit()

    return None  # 204 No Content

# ==================== PRODUCTS MANAGEMENT =====================
@router.get("/{campaign_id}/products", response_model=List[dict])
def list_campaign_products(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all products linked to campaign.
    
    Path params:
    - campaign_id: ID of the campaign

    Returns:
    - List of products with details
    """
    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # get all linked products
    from app.models.campaign import CampaignProduct
    from app.models.product import Product

    campaign_products = db.query(CampaignProduct).filter(
        CampaignProduct.campaign_id == campaign_id
    ).all()

    # Build response with product details
    result = []
    for cp in campaign_products:
        product = db.query(Product).filter(Product.id == cp.product_id).first()
        if product:
            result.append({
                "product_id": product.id,
                "name": product.name,
                "short_description": product.short_description,
                "item_number": product.item_number,
                "added_at": cp.added_at
            })
    return result

@router.post("/{campaign_id}/products", status_code=status.HTTP_201_CREATED)
def add_product_to_campaign(
    campaign_id: int, 
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a product to a campaign.

    Path params:
    - campaign_id: ID of the campaign

    Query params:
    - product_id: ID of the product to add

    Returns:
    - 201 Created on success
    """
    from app.models.campaign import CampaignProduct
    from app.models.product import Product

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # Check if product exists and belongs to user
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")
    
    # Check if already linked
    existing = db.query(CampaignProduct).filter(
        CampaignProduct.campaign_id == campaign_id,
        CampaignProduct.product_id == product_id
    ).first()

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {product_id} is already linked to campaign {campaign_id}")
    
    # Create link
    campaign_product = CampaignProduct(
        campaign_id=campaign_id,
        product_id=product_id
    )

    db.add(campaign_product)
    db.commit()
    db.refresh(campaign_product)

    return {
        "message": "Product added to campaign successfully",
        "product_id": product_id,
        "campaign_id": campaign_id
    }

@router.post("/{campaign_id}/products/bulk", status_code=status.HTTP_201_CREATED)
def add_campaign_products_bulk(
    campaign_id: int,
    product_ids: List[int], 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add multiple products to a campaign in bulk.

    Path params:
    - campaign_id: ID of the campaign

    Body:
    [123, 456, 789]

    Returns:
    - Summary of added/skipped products

    """
    from app.models.campaign import CampaignProduct
    from app.models.product import Product

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    added = []
    skipped = []
    not_found = []

    for product_id in product_ids:
        # Check if product exists and belongs to user
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.user_id == current_user.id
        ).first()

        if not product:
            not_found.append(product_id)
            continue

        # Check if already linked
        existing = db.query(CampaignProduct).filter(
            CampaignProduct.campaign_id == campaign_id,
            CampaignProduct.product_id == product_id
        ).first()

        if existing:
            skipped.append(product_id)
            continue

        # Create link
        campaign_product = CampaignProduct(
            campaign_id=campaign_id,
            product_id=product_id
        )

        db.add(campaign_product)
        added.append(product_id)

    db.commit()

    return {
        "message": f"Added {len(added)} products",
        "added": added,
        "skipped": skipped,
        "not_found": not_found
    }

@router.delete("/{campaign_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_from_campaign(
    campaign_id: int,
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a product from a campaign.

    Path params:
    - campaign_id: ID of the campaign
    - product_id: ID of the product to remove

    Returns:
    - 204 No Content on success
    """
    from app.models.campaign import CampaignProduct

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # Get link
    campaign_product = db.query(CampaignProduct).filter(
        CampaignProduct.campaign_id == campaign_id,
        CampaignProduct.product_id == product_id
    ).first()

    if not campaign_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} is not linked to campaign {campaign_id}")
    
    db.delete(campaign_product)
    db.commit()

    return None  # 204 No Content

# ==================== CAMPAIGN STATISTICS =====================
@router.get("/{campaign_id}/stats")
def get_campaign_stats(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about a campaign, such as number of contacts, status breakdown, etc.

    Path params:
    - campaign_id: ID of the campaign

    Returns:
    - Statistics about the campaign
    """
    from app.models.campaign import CampaignContact, CampaignProduct
    from sqlalchemy import func

    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_id} not found")
    
    # Get all contacts for this campaign
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    ).all()

    # Count contacts by status
    status_counts = {}
    total_contacts = len(contacts)

    for contact in contacts:
        status = contact.status or "pending"
        status_counts[status] = status_counts.get(status, 0) + 1

    # Email sequence stats
    total_emails_sent = sum(c.email_sequence_step for c in contacts if c.email_sequence_step)
    avg_email_step = (total_emails_sent / total_contacts) if total_contacts > 0 else 0

    # Get last email sent timestamp
    last_email_sent = None 
    for contact in contacts:
        if contact.last_email_sent_at:
            if last_email_sent is None or contact.last_email_sent_at > last_email_sent:
                last_email_sent = contact.last_email_sent_at
    
    # Get product count
    product_count = db.query(CampaignProduct).filter(
        CampaignProduct.campaign_id == campaign_id
    ).count()

    return {
        "campaign": {
            "id": campaign.id,
            "name": campaign.name,
            "event_date": campaign.event_date,
            "end_date": campaign.end_date,
            "location": campaign.location,
            "distributor_name": campaign.distributor_name,
            "status": campaign.status.value,
            "created_at": campaign.created_at,
        },
        "contacts": {
            "total": total_contacts,
            "by_status": status_counts,
        },
        "products": {
            "total": product_count
        },
        "email_sequence": {
            "total_emails_sent": total_emails_sent,
            "avg_step": (avg_email_step, 2),
            "last_sent": last_email_sent        
        }
    }

