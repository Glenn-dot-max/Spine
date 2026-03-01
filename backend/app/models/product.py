"""
Product model.
"""
from sqlalchemy import String, Text, ForeignKey, Index
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
    
    item_number: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relations
    user: Mapped["User"] = relationship(back_populates="products")
    
    # Unique constraint par user
    __table_args__ = (
        Index('ix_products_user_item', 'user_id', 'item_number', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<Product {self.item_number} - {self.name}>"
