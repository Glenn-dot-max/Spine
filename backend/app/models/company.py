"""
Company model - represents a business entity linked to prospects.
"""

from sqlalchemy import String, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
import enum

from app.models.base import Base, TimestampMixin

class StructureType(str, enum.Enum):
    retail = "retail"
    foodservice = "foodservice"
    industry = "industry"
    other = "other"

class ContactType(str, enum.Enum):
    distributor = "distributor"
    restaurant = "restaurant"
    factory = "factory"
    consultant = "consultant"
    retailer = "retailer"
    other = "other"

class Company(Base, TimestampMixin):
    """Business entity that can be linked to multiple prospects."""
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

    # Classification
    type_structure: Mapped[Optional[StructureType]] = mapped_column(
        Enum(StructureType),
        nullable=True
    )
    type_contact: Mapped[Optional[ContactType]] = mapped_column(
        Enum(ContactType),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="companies")
    prospects: Mapped[List["Prospect"]] = relationship(back_populates="company")

    __table_args__ = (
        Index("ix_companies_user_id_name", "user_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.type_structure})>"