"""
API routes for Product management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Product as ProductModel
from app.schemas import Product, ProductCreate, ProductUpdate
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/products", tags=["products"])

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product (protected)."""
    existing = db.query(ProductModel).filter(
        ProductModel.item_number == product.item_number,
        ProductModel.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with item number {product.item_number} already exists"
        )
    
    db_product = ProductModel(
        **product.model_dump(),
        user_id=current_user.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[Product])
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all products for the current user (protected)."""
    products = db.query(ProductModel).filter(ProductModel.user_id == current_user.id).all()
    return products

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single product by ID (protected)."""
    product = db.query(ProductModel).filter(
        ProductModel.id == product_id,
        ProductModel.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return product

@router.patch("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product by ID (protected)."""
    db_product = db.query(ProductModel).filter(
        ProductModel.id == product_id,
        ProductModel.user_id == current_user.id
    ).first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product by ID (protected)."""
    db_product = db.query(ProductModel).filter(
        ProductModel.id == product_id,
        ProductModel.user_id == current_user.id
    ).first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    db.delete(db_product)
    db.commit()
    return None