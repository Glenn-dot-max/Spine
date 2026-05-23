"""
API routes for company management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models.company import Company as CompanyModel
from app.schemas.company import Company, CompanyCreate, CompanyUpdate
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/companies", tags=["companies"])

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

@router.get("/", response_model=List[Company])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(CompanyModel).filter(CompanyModel.user_id == current_user.id).all()

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

