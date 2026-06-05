"""
SPINE V1 — Schemas DistributorCatalog
==========================
Rôle : Validation et sérialisation des catalogues distributeurs
Dépendances : schemas/product.py
Utilisé par : routes/distributor_catalogs.py
Dernière modification : 2026-06-02 — Création
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Items (produits dans un catalogue) ---

class DistributorCatalogItemBase(BaseModel):
    product_id: int
    notes: Optional[str] = None
    is_active: bool = True

class DistributorCatalogItemCreate(DistributorCatalogItemBase):
    pass

class DistributorCatalogItemUpdate(BaseModel):
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class DistributorCatalogItemOut(DistributorCatalogItemBase):
    id: int
    catalog_id: int
    created_at: datetime
    # Infos produit dénormalisées pour éviter un 2e appel API
    product_name: Optional[str] = None
    product_item_number: Optional[str] = None
    product_brand: Optional[str] = None
    product_category: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Catalogue ---

class DistributorCatalogBase(BaseModel):
    name: str
    notes: Optional[str] = None

class DistributorCatalogCreate(DistributorCatalogBase):
    company_id: int

class DistributorCatalogUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None

class DistributorCatalogOut(DistributorCatalogBase):
    id: int
    user_id: int
    company_id: int
    created_at: datetime
    items: List[DistributorCatalogItemOut] = []
    pdf_filename: Optional[str] = None
    has_pdf: bool = False

    model_config = {"from_attributes": True}

class DistributorCatalogSummary(DistributorCatalogBase):
    """Version légère sans les items — pour les listes."""
    id: int
    company_id: int
    item_count: int = 0
    pdf_filename: Optional[str] = None
    has_pdf: bool = False

    model_config = {"from_attributes": True}