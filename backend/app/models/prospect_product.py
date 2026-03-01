"""
Association table for Prospect-Product many-to-many relationship.
"""
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base import Base, TimestampMixin


class ProspectProduct(Base, TimestampMixin):
    """Link between prospect and product (with notes)."""
    
    __tablename__ = "prospect_products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relations (NO back_populates pour Product car Product n'a pas besoin de cette relation)
    prospect: Mapped["Prospect"] = relationship(back_populates="product_interests")
    
    def __repr__(self) -> str:
        return f"<ProspectProduct prospect_id={self.prospect_id} product_id={self.product_id}>"