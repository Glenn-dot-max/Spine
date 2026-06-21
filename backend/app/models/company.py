"""
SPINE V1 - company model
========================
Role: Business entity in the food distribution chain. 
      Two-level qualification:
        1. chain_level : position in the distribution chain
        2. end_user_type: sub-type when chain_level = end_user
Dependencies: app.models.base
Used by: routes/companies.py, routes/campaigns.py
Security: user_is required in all queries.
Last modified: 2026 - 06 - 21 - chain_level + end_user_type replace type_structure/type_contact
"""
from sqlalchemy import String, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
import enum

from app.models.base import Base, TimestampMixin

class ChainLevel(str, enum.Enum):
    """Position of the company in the food distribution chain."""
    distributor = "distributor"    # Sysco, US Foods, etc.
    importer = "importer"          # Imports from abroad
    broker = "broker"              # Intermediary / rep
    end_user = "end_user"          # Final buyer (restaurant, hotel, etc.)
    other = "other"

class EndUserType(str, enum.Enum):
    """Sub-type when chain_level = end_user."""
    restaurant = "restaurant"
    hotel = "hotel"
    franchise = "franchise"
    country_club = "country_club"
    catering = "catering"
    institutional = "institutional"
    retail = "retail"
    other = "other"

class Company(Base, TimestampMixin):
    """Business entity that can be linked to prospects."""
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True 
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    market: Mapped[Optional[str]] = mapped_column(String(100))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Classification - Level 1 : position in the distribution chain
    chain_level: Mapped[Optional[ChainLevel]] = mapped_column(
        Enum(ChainLevel), nullable=True
    )

    # Classification - Level 2 : sub-type (only relevant when chain_level = end_user)
    end_user_type: Mapped[Optional[EndUserType]] = mapped_column(
        Enum(EndUserType), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="companies")
    prospects: Mapped[List["Prospect"]] = relationship(back_populates="company")
    distributor_catalog: Mapped[Optional["DistributorCatalog"]] = relationship(
        back_populates="company", 
        uselist=False,
    )

    __table_args__ = (
        Index("ix_companies_user_id_name", "user_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.chain_level})>"
