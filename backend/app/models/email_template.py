"""
Email Template model for customizable email templates. 
"""
from sqlalchemy import String, Text, Boolean, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any

from app.models.base import Base, TimestampMixin

class EmailTemplate(Base, TimestampMixin):
    """
    Email template with variable substitution support. 
    Can be user-specific or global (user_id = null).
    """
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Owner (null = template glbal pour tous)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Template identification
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Template content
    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    # Unique constraint
    __table_args__ = (
        Index('ix_email_templates_user_id_name_category', 'user_id', 'name', 'category'),
    )

    def __repr__(self) -> str:
        owner = f"User {self.user_id}" if self.user_id else "Global"
        return f"<EmailTemplate {self.name} ({owner})>"