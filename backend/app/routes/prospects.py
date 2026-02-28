"""
API routes for prospect management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Prospect as ProspectModel, Product as ProductModel, ProspectProduct
from app.schemas import (
    Prospect,
    ProspectCreate,
    ProspectUpdate,
    ProspectProductLink
)

router = APIRouter(prefix="/api/prospects", tags=["prospects"])

@router.post("/", response_model=Prospect, status_code=status.HTTP_201_CREATED)
def create_prospect(prospect: ProspectCreate, db: Session = Depends(get_db)):
    """Create a new prospect with optional product interests."""
    existing = db.query(ProspectModel).filter(
        ProspectModel.email == prospect.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prospect with email {prospect.email} already exists"
        )
    
    # Create the prospect
    prospect_data = prospect.model_dump(exclude={"product_interest_ids"})
    db_prospect = ProspectModel(**prospect_data)
    db.add(db_prospect)
    db.flush()  # Get ID before commit

    if prospect.product_interest_ids:
        for product_id in prospect.product_interest_ids:
            product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
            if not product:
                db.rollback()  # Rollback prospect creation if product is invalid
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} does not exist"
                )
            link = ProspectProduct(prospect_id=db_prospect.id, product_id=product_id)
            db.add(link)
    
    db.commit()
    db.refresh(db_prospect)
    return db_prospect

@router.get("/", response_model=List[Prospect])
def list_prospects(
    skip: int = 0,
    limit: int = 100,
    source: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all prospects with pagination and optional filters."""
    query = db.query(ProspectModel)

    if source:
        query = query.filter(ProspectModel.source == source)
    if status:
        query = query.filter(ProspectModel.status == status)

    prospects = query.offset(skip).limit(limit).all()
    return prospects

@router.get("/{prospect_id}", response_model=Prospect)
def get_prospect(prospect_id: int, db: Session = Depends(get_db)):
    """Get a specific prospect by ID."""
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect with ID {prospect_id} not found")
    return prospect

@router.patch("/{prospect_id}", response_model=Prospect)
def update_prospect(prospect_id: int, prospect_update: ProspectUpdate, db: Session = Depends(get_db)):
    """Update a prospect (partial update)."""
    db_prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()

    if not db_prospect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect with ID {prospect_id} not found")
    
    update_data = prospect_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_prospect, field, value)

    db.commit()
    db.refresh(db_prospect)
    return db_prospect

@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prospect(prospect_id: int, db: Session = Depends(get_db)):
    """Delete a prospect."""
    db_prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not db_prospect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect with ID {prospect_id} not found")
    
    db.delete(db_prospect)
    db.commit()
    return None

@router.post("/{prospect_id}/products", status_code=status.HTTP_201_CREATED)
def add_product_interest(
    prospect_id: int,
    link: ProspectProductLink,
    db: Session = Depends(get_db)
):
    """Link a prospect to a product of interest."""
    # Verify prospect exists
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect with ID {prospect_id} not found")
    
    # Verify product exists
    product = db.query(ProductModel).filter(ProductModel.id == link.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {link.product_id} not found")
    
    # Check if link already exists
    existing_link = db.query(ProspectProduct).filter(
        ProspectProduct.prospect_id == prospect_id,
        ProspectProduct.product_id == link.product_id
    ).first()

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prospect with ID {prospect_id} is already linked to product with ID {link.product_id}"
        )
    
    # Create the link
    db_link = ProspectProduct(
        prospect_id=prospect_id,
        product_id=link.product_id,
        notes=link.notes
    )
    db.add(db_link)
    db.commit()

    return {"message": f"Prospect with ID {prospect_id} linked to product with ID {link.product_id} successfully"}

@router.get("/{prospect_id}/products")
def get_prospect_products(prospect_id: int, db: Session = Depends(get_db)):
    """Get all products linked to a prospect."""
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prospect with ID {prospect_id} not found")
    
    products = db.query(ProductModel).join(ProspectProduct).filter(ProspectProduct.prospect_id == prospect_id).all()

    return products