"""
ProspectProduct model - links prospects to products of interest.
"""
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class ProspectProduct(Base):
    """
    Many-to-many relationship between Prospects and Products.

    Represents products that a prospect is interested in.
    Used to personalize email template with relevant products.
    """
    __tablename__ = "prospect_products"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    # Metadata
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    prospect = relationship("Prospect", back_populates="product_interests")
    product = relationship("Product", back_populates="prospect_interests")

    # Constraints
    __table_args__ = (
        UniqueConstraint("prospect_id", "product_id", name="uix_prospect_product"),
    )

    def __repr__(self) -> str:
        return f"<ProspectProduct(prospect_id={self.prospect_id}, product_id={self.product_id})>"
    