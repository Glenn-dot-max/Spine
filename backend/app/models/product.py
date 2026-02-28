"""
Product model - represents items from user's product catalog.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Product(Base, TimestampMixin):
    """
    Product catalog entry.

    Products are imported via CSV (initially) or PDF parsing (later).
    Used to personalize email templates with product information.

    Attributes:
        item_number: Unique product identifier (SKU).
        name: Product name.
        short_description: Brief product description.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    item_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Product SKU item code"
    )
    name = Column(String(255), nullable=False, comment="Product name")
    short_description = Column(Text, nullable=True, comment="Brief product description")

    # Relationships
    prospect_interests = relationship(
        "ProspectProduct",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, item_number='{self.item_number}', name='{self.name}')>"