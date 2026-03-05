"""
API routes for prospect management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Prospect as ProspectModel
from app.schemas import Prospect, ProspectCreate, ProspectUpdate
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/prospects", tags=["prospects"])

@router.post("/", response_model=Prospect, status_code=status.HTTP_201_CREATED)
def create_prospect(
  prospect: ProspectCreate,
  current_user: User = Depends(get_current_user),
  db: Session = Depends(get_db)
):
  """Create a neww prospect (protected)."""
  db_prospect = ProspectModel(
    **prospect.model_dump(),
    user_id=current_user.id
  )
  db.add(db_prospect)
  db.commit()
  db.refresh(db_prospect)
  return db_prospect

@router.get("/", response_model=List[Prospect])
def list_prospects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    """List all prospects for the current user (protected)."""
    prospects = db.query(ProspectModel).filter(ProspectModel.user_id == current_user.id).all()
    return prospects

@router.get("/{prospect_id}", response_model=Prospect)
def get_prospect(
    prospect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single prospect by ID (protected)."""
    prospect = db.query(ProspectModel).filter(
        ProspectModel.id == prospect_id,
        ProspectModel.user_id == current_user.id
    ).first()

    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID {prospect_id} not found"
        )
    
    return prospect

@router.put("/{prospect_id}", response_model=Prospect)
def update_prospect(
    prospect_id: int, 
    prospect_update: ProspectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a prospect (protected)."""
    db_prospect = db.query(ProspectModel).filter(
        ProspectModel.id == prospect_id,
        ProspectModel.user_id == current_user.id
    ).first()

    if not db_prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID {prospect_id} not found"
        )
    
    update_data = prospect_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_prospect, field, value)
    
    db.commit()
    db.refresh(db_prospect)
    return db_prospect

@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prospect(
    prospect_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a prospect (protected)."""
    db_prospect = db.query(ProspectModel).filter(
        ProspectModel.id == prospect_id,
        ProspectModel.user_id == current_user.id
    ).first()

    if not db_prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID {prospect_id} not found"
        )
    
    db.delete(db_prospect)
    db.commit()
    return None