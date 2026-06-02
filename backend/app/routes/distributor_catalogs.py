"""
SPINE V1 — Routes DistributorCatalog
==========================
Rôle : CRUD catalogues distributeurs + ajout/retrait produits + fallback général
Dépendances : models/distributor_catalog.py, schemas/distributor_catalog.py
Utilisé par : routes/__init__.py
Sécurité : user_id filtré sur toutes les requêtes
À faire : /
Dernière modification : 2026-06-02 — Création
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.distributor_catalog import DistributorCatalog, DistributorCatalogItem
from app.models.product import Product
from app.schemas.distributor_catalog import (
    DistributorCatalogCreate,
    DistributorCatalogUpdate,
    DistributorCatalogOut,
    DistributorCatalogSummary,
    DistributorCatalogItemCreate,
    DistributorCatalogItemUpdate,
    DistributorCatalogItemOut,
)

router = APIRouter(prefix="/api/distributor-catalogs", tags=["distributor-catalogs"])


def _serialize_item(item: DistributorCatalogItem) -> DistributorCatalogItemOut:
    """Sérialise un item avec les infos produit dénormalisées."""
    return DistributorCatalogItemOut(
        id=item.id,
        catalog_id=item.catalog_id,
        product_id=item.product_id,
        notes=item.notes,
        is_active=item.is_active,
        created_at=item.created_at,
        product_name=item.product.name if item.product else None,
        product_item_number=item.product.item_number if item.product else None,
        product_brand=item.product.brand if item.product else None,
        product_category=item.product.category if item.product else None,
    )


# --- CRUD Catalogue ---

@router.get("/", response_model=List[DistributorCatalogSummary])
def list_catalogs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste tous les catalogues distributeurs de l'utilisateur."""
    catalogs = db.query(DistributorCatalog).filter(
        DistributorCatalog.user_id == current_user.id
    ).all()

    result = []
    for catalog in catalogs:
        item_count = db.query(DistributorCatalogItem).filter(
            DistributorCatalogItem.catalog_id == catalog.id
        ).count()
        result.append(DistributorCatalogSummary(
            id=catalog.id,
            company_id=catalog.company_id,
            name=catalog.name,
            notes=catalog.notes,
            item_count=item_count,
        ))
    return result


@router.post("/", response_model=DistributorCatalogOut, status_code=201)
def create_catalog(
    payload: DistributorCatalogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crée un catalogue pour un distributeur (company_id)."""
    # Vérifier que la company appartient à l'user
    from app.models.company import Company
    company = db.query(Company).filter(
        Company.id == payload.company_id,
        Company.user_id == current_user.id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Vérifier qu'un catalogue n'existe pas déjà pour ce distributeur
    existing = db.query(DistributorCatalog).filter(
        DistributorCatalog.user_id == current_user.id,
        DistributorCatalog.company_id == payload.company_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Un catalogue existe déjà pour ce distributeur (id={existing.id})"
        )

    catalog = DistributorCatalog(
        user_id=current_user.id,
        company_id=payload.company_id,
        name=payload.name,
        notes=payload.notes,
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    return DistributorCatalogOut(
        id=catalog.id,
        user_id=catalog.user_id,
        company_id=catalog.company_id,
        name=catalog.name,
        notes=catalog.notes,
        created_at=catalog.created_at,
        items=[],
    )


@router.get("/{catalog_id}", response_model=DistributorCatalogOut)
def get_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne un catalogue avec tous ses produits."""
    catalog = db.query(DistributorCatalog).options(
        joinedload(DistributorCatalog.items).joinedload(DistributorCatalogItem.product)
    ).filter(
        DistributorCatalog.id == catalog_id,
        DistributorCatalog.user_id == current_user.id,
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    return DistributorCatalogOut(
        id=catalog.id,
        user_id=catalog.user_id,
        company_id=catalog.company_id,
        name=catalog.name,
        notes=catalog.notes,
        created_at=catalog.created_at,
        items=[_serialize_item(item) for item in catalog.items],
    )


@router.patch("/{catalog_id}", response_model=DistributorCatalogOut)
def update_catalog(
    catalog_id: int,
    payload: DistributorCatalogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met à jour le nom ou les notes d'un catalogue."""
    catalog = db.query(DistributorCatalog).filter(
        DistributorCatalog.id == catalog_id,
        DistributorCatalog.user_id == current_user.id,
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    if payload.name is not None:
        catalog.name = payload.name
    if payload.notes is not None:
        catalog.notes = payload.notes

    db.commit()
    db.refresh(catalog)
    return get_catalog(catalog_id, db, current_user)


@router.delete("/{catalog_id}", status_code=204)
def delete_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime un catalogue et tous ses items (cascade)."""
    catalog = db.query(DistributorCatalog).filter(
        DistributorCatalog.id == catalog_id,
        DistributorCatalog.user_id == current_user.id,
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    db.delete(catalog)
    db.commit()


# --- Gestion des produits dans un catalogue ---

@router.post("/{catalog_id}/items", response_model=DistributorCatalogItemOut, status_code=201)
def add_product_to_catalog(
    catalog_id: int,
    payload: DistributorCatalogItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ajoute un produit au catalogue distributeur."""
    catalog = db.query(DistributorCatalog).filter(
        DistributorCatalog.id == catalog_id,
        DistributorCatalog.user_id == current_user.id,
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    # Vérifier que le produit appartient à l'user
    product = db.query(Product).filter(
        Product.id == payload.product_id,
        Product.user_id == current_user.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Vérifier que le produit n'est pas déjà dans le catalogue
    existing = db.query(DistributorCatalogItem).filter(
        DistributorCatalogItem.catalog_id == catalog_id,
        DistributorCatalogItem.product_id == payload.product_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Product already in catalog")

    item = DistributorCatalogItem(
        catalog_id=catalog_id,
        product_id=payload.product_id,
        notes=payload.notes,
        is_active=payload.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item.product = product
    return _serialize_item(item)


@router.patch("/{catalog_id}/items/{item_id}", response_model=DistributorCatalogItemOut)
def update_catalog_item(
    catalog_id: int,
    item_id: int,
    payload: DistributorCatalogItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met à jour les notes ou le statut actif d'un item."""
    # Vérifier ownership via le catalogue
    catalog = db.query(DistributorCatalog).filter(
        DistributorCatalog.id == catalog_id,
        DistributorCatalog.user_id == current_user.id,
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    item = db.query(DistributorCatalogItem).options(
        joinedload(DistributorCatalogItem.product)
    ).filter(
        DistributorCatalogItem.id == item_id,
        DistributorCatalogItem.catalog_id == catalog_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.notes is not None:
        item.notes = payload.notes
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    db.refresh(item)
    return _serialize_item(item)


@router.delete("/{catalog_id}/items/{item_id}", status_code=204)
def remove_product_from_catalog(
    catalog_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retire un produit du catalogue distributeur."""
    catalog = db.query(DistributorCatalog).filter(
        DistributorCatalog.id == catalog_id,
        DistributorCatalog.user_id == current_user.id,
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    item = db.query(DistributorCatalogItem).filter(
        DistributorCatalogItem.id == item_id,
        DistributorCatalogItem.catalog_id == catalog_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()


# --- Endpoint fallback : produits disponibles pour un distributeur ---

@router.get("/by-company/{company_id}/products", response_model=List[dict])
def get_products_for_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les produits disponibles pour un distributeur.
    - Si un catalogue distributeur existe → retourne ses produits actifs
    - Sinon → retourne tout le catalogue général de l'user
    """
    catalog = db.query(DistributorCatalog).filter(
        DistributorCatalog.user_id == current_user.id,
        DistributorCatalog.company_id == company_id,
    ).first()

    if catalog:
        items = db.query(DistributorCatalogItem).options(
            joinedload(DistributorCatalogItem.product)
        ).filter(
            DistributorCatalogItem.catalog_id == catalog.id,
            DistributorCatalogItem.is_active == True,
        ).all()
        return [
            {
                "id": item.product.id,
                "item_number": item.product.item_number,
                "name": item.product.name,
                "brand": item.product.brand,
                "category": item.product.category,
                "source": "distributor_catalog",
            }
            for item in items if item.product
        ]
    else:
        products = db.query(Product).filter(
            Product.user_id == current_user.id,
            Product.is_active == True,
        ).all()
        return [
            {
                "id": p.id,
                "item_number": p.item_number,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "source": "general_catalog",
            }
            for p in products
        ]