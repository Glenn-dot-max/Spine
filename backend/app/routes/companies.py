"""
SPINE V1 - companies (routes)
===========================
Rôle: CRUD des entreprises + lookup contacts par company
Dépendances: models/company.py, models/prospect.py, schemas/company.py
Utilisé par: frontend Companies.tsx, CreateCampaignWizard.tsx
Sécurité: user_id filtré sur toutes les requêtes SQL
A faire : -
Dernière modification : 2026-06-21 - ajout filtre chain_level + endpoints /contacts
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models.company import Company as CompanyModel, ChainLevel
from app.models.prospect import Prospect as ProspectModel
from app.schemas.company import CompanyCreate, CompanyUpdate, Company
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/companies", tags=["companies"])

# -- CREATE ----------------------------------------------------

@router.post("/", response_model=Company, status_code=status.HTTP_201_CREATED)
def create_company(
    company: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_company = CompanyModel(**company.model_dump(), user_id=current_user.id)
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# -- LIST (avec filtre optionnel chain_level) ------------------------------------------------------

@router.get("/", response_model=List[Company])
def list_companies(
    chain_level: Optional[ChainLevel] = Query(None, description="Filter by chain level"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's companies.
    Optional query parameter `chain_level` allows filtering by position in the distribution chain.
    Example : GET /api/companies/?chain_level=distributor
    """
    q = db.query(CompanyModel).filter(CompanyModel.user_id == current_user.id)
    if chain_level:
        q = q.filter(CompanyModel.chain_level == chain_level)
    return q.order_by(CompanyModel.name).all()

# -- GET single ------------------------------------------------

@router.get("/{company_id}", response_model=Company)
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(CompanyModel).filter(
        CompanyModel.id == company_id,
        CompanyModel.user_id == current_user.id
    ).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company

# -- COMPANY CONTACTS (prospects linked to this company) ------------------------------------------------

@router.get("/{company_id}/contacts")
def get_company_contacts(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all prospects linked to a company.
    """
    company = db.query(CompanyModel).filter(
        CompanyModel.id == company_id,
        CompanyModel.user_id == current_user.id
    ).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    
    contacts = db.query(ProspectModel).filter(
        ProspectModel.company_id == company_id,
        ProspectModel.user_id == current_user.id
    ).order_by(ProspectModel.last_name).all()

    return [
        {
            "id": c.id,
            "first_name": c.first_name or "",
            "last_name": c.last_name or "",
            "email": c.email,
            "position": c.position or "",
        }
        for c in contacts
    ]

# -- UPDATE ------------------------------------------------

@router.put("/{company_id}", response_model=Company)
def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_company = db.query(CompanyModel).filter(
        CompanyModel.id == company_id,
        CompanyModel.user_id == current_user.id
    ).first()
    if not db_company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    
    for field, value in company_update.model_dump(exclude_unset=True).items():
        setattr(db_company, field, value)

    db.commit()
    db.refresh(db_company)
    return db_company

# -- DELETE ------------------------------------------------

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_company = db.query(CompanyModel).filter(
        CompanyModel.id == company_id,
        CompanyModel.user_id == current_user.id
    ).first()
    if not db_company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    
    db.delete(db_company)
    db.commit()
    return None