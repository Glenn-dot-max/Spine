"""
SPINE V1 - Product model
==========================
Rôle : Catalogue produits du sales rep (général + par distributeur)
Dépendances : models/base.py, models/user.py
Utilisé par :routes/products.py, routes/product_import.py
Sécurité : user_id filtré sur toutes les requêtes
A faire : Lisaison DistributorCatalog (Sprint 3 tâche 3)
Denière modification : 2026-05-20 - Création du modèle
"""
from sqlalchemy import String, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base import Base, TimestampMixin

class Product(Base, TimestampMixin):
    """Product in catalog."""
    
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Owner
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Indentification
    item_number: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(255))

    # Description
    short_description: Mapped[Optional[str]] = mapped_column(Text)

    # Food distributon specifics
    category: Mapped[Optional[str]] = mapped_column(String(100))
    formats: Mapped[Optional[str]] = mapped_column(String(500))
    price_range: Mapped[Optional[str]] = mapped_column(String(100))
    certifications: Mapped[Optional[str]] = mapped_column(String(500))
    segments: Mapped[Optional[str]] = mapped_column(String(255))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relations
    user: Mapped["User"] = relationship(back_populates="products")

    # Unique constraint par user
    __table_args__ = (
        Index('ix_products_user_item', 'user_id', 'item_number', unique=True),
    )

    def __repr__(self) -> str:
        return f"<Product {self.item_number} - {self.name}>"
