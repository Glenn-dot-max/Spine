"""
API routes for managing Prospect-Product relationships.
handles product interests for prospects.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import (
    Prospect as ProspectModel,
    Product as ProductModel,
    ProspectProduct as ProspectProductModel
)
from app.schemas import ProspectProductLink, ProspectProductResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.services.permissions import verify_resource_ownership

router = APIRouter(
    prefix="/api/prospects/{prospect_id}/products",
    tags=["prospect-products"]
)

@router.post("/", response_model=ProspectProductResponse,
status_code=status.HTTP_201_CREATED)
def add_product_interest(
    prospect_id: int, 
    link_data: ProspectProductLink,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a product interest to a prospect. 

    The product will be linked to the prospect with optional notes. 
    Both prospect and product must belong to the current user. 
    """
    # Verify prospect ownership
    prospect = verify_resource_ownership(
        db.query(ProspectModel).filter(
            ProspectModel.id == prospect_id
        ).first(),
        current_user.id,
        "Prospect"
    )

    # Verify product ownership
    product = verify_resource_ownership(
        db.query(ProductModel).filter(
            ProductModel.id == link_data.product_id
        ).first(),
        current_user.id,
        "Product"
    )

    # Check if link already exists
    existing_link = db.query(ProspectProductModel).filter(
        ProspectProductModel.prospect_id == prospect_id,
        ProspectProductModel.product_id == link_data.product_id
    ).first()

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This product is already linked to the prospect"
        )
    
    # Create new link
    db_link = ProspectProductModel(
        prospect_id=prospect_id,
        product_id=link_data.product_id,
        notes=link_data.notes
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    return db_link

@router.get("/", response_model=List[ProspectProductResponse])
def list_product_interests(
    prospect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all product interests for a prospect. 

    Returns all products linked to this prospect.
    """
    # Verify prospect ownership
    verify_resource_ownership(
        db.query(ProspectModel).filter(
            ProspectModel.id == prospect_id
        ).first(),
        current_user.id,
        "Prospect"
    )

    # Get all links
    links = db.query(ProspectProductModel).filter(
        ProspectProductModel.prospect_id == prospect_id
    ).all()

    return links


@router.patch("/{product_id}", response_model=ProspectProductResponse)
def update_product_interest_notes(
    prospect_id: int,
    product_id: int,
    link_data: ProspectProductLink,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates notes for a product interest.
    
    Allows updating only the notes field of the link.
    """
    # Verify prospect ownership
    verify_resource_ownership(
        db.query(ProspectModel).filter(
            ProspectModel.id == prospect_id
        ).first(),
        current_user.id,
        "Prospect"
    )

    # Verify product ownership
    verify_resource_ownership(
        db.query(ProductModel).filter(
            ProductModel.id == product_id
        ).first(),
        current_user.id,
        "Product"
    )

    # Get link
    db_link = db.query(ProspectProductModel).filter(
        ProspectProductModel.prospect_id == prospect_id,
        ProspectProductModel.product_id == product_id
    ).first()

    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product interest link not found"
        )
    
    # Update notes
    db_link.notes = link_data.notes
    db.commit()
    db.refresh(db_link)

    return db_link

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_interest(
    prospect_id: int, 
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a product interest from a prospect.

    Deletes the link between the prospect and product.
    """
    # verify prospect ownership
    verify_resource_ownership(
        db.query(ProspectModel).filter(
            ProspectModel.id == prospect_id
        ).first(),
        current_user.id,
        "Prospect"
    )

    # verify product ownership
    verify_resource_ownership(
        db.query(ProductModel).filter(
            ProductModel.id == product_id
        ).first(),
        current_user.id,
        "Product"
    )

    # Get and delete link
    db_link = db.query(ProspectProductModel).filter(
        ProspectProductModel.prospect_id == prospect_id,
        ProspectProductModel.product_id == product_id
    ).first()

    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product interest link not found"
        )
    
    db.delete(db_link)
    db.commit()

    return None  # 204 No Content response

