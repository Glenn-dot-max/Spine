"""
User model for authentication
"""

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.db import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.prospect import Prospect

class User(Base):
    __tablename__ = "users"

    # Base fields

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Gmail Oauth fields
    gmail_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    gmail_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gmail_access_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gmail_refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Outlook Oauth fields
    outlook_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    outlook_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    outlook_access_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    outlook_refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Default provider
    default_email_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    prospects: Mapped[list["Prospect"]] = relationship("Prospect", back_populates="user", cascade="all, delete-orphan")

    @property
    def has_email_configured(self) -> bool:
        """Check if the user has at least one email provider configured."""
        return self.gmail_connected or self.outlook_connected
    
    @property
    def primary_email_address(self) -> Optional[str]:
        """Return the primary email address based on the default provider."""
        if self.default_email_provider == "gmail" and self.gmail_connected:
            return self.gmail_email
        elif self.default_email_provider == "outlook" and self.outlook_connected:
            return self.outlook_email
        elif self.gmail_connected:
            return self.gmail_email
        elif self.outlook_connected:
            return self.outlook_email
        return None