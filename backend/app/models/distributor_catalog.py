"""
SPINE V1 - DistributorCatalog model
==========================
Rôle : Sous-catalogue de produits associé à un distributeur (Company)
Dépendances : models/base.py, models/company.py, models/product.py
Utilisé par : routes/distributor_catalog.py
Sécurité : user_id filtré sur toutes les requêtes - jamais de catalogue cross-user.
À faire : /
Dernière modification : 2026-06-02 - Création du modèle
"""
from sqlalchemy import String, Text, ForeignKey, Index, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from app.models.base import Base, TimestampMixin

class DistributorCatalog(Base, TimestampMixin):
    """
    Catalogue de produits dédié à un distributeur spécifique.
    Un distributeur (Company) peut avoir un seul catalogue actif par user.
    Si aucun catalogue n'exuste pour ce distributeur, on utilise le catalogue général.
    """
    __tablename__ = "distributor_catalogs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Owner and association
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # PDF lié au catalogue (stocké dans /tmp/spine_catalogs/{catalog_id}/)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="distributor_catalog")
    items: Mapped[List["DistributorCatalogItem"]] = relationship(
        back_populates="catalog",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_catalog_user_company"),
        Index("ix_distributor_catalogs_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<DistributorCatalog {self.name} (company_id={self.company_id})>"
    
  
class DistributorCatalogItem(Base, TimestampMixin):
    """
    Ligne d'un catalogue distributeur - association produit <-> catalogue.
    Permet d'ajouter des notes spécifiques par produit pour ce distributeur.
    """
    __tablename__ = "distributor_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    catalog_id: Mapped[int] = mapped_column(
        ForeignKey("distributor_catalogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    catalog: Mapped["DistributorCatalog"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


    __table_args__ = (
        UniqueConstraint("catalog_id", "product_id", name="uq_catalog_item_product"),
    )

    def __repr__(self) -> str:
        return f"<DistributorCatalogItem catalog_id={self.catalog_id} product_id={self.product_id} active={self.is_active}>"