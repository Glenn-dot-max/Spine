"""
Prospect model - represents leads from various sources.
"""

from sqlalchemy import Column, Integer, String, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from enum import Enum
from .base import Base, TimestampMixin

class ProspectSource(str, Enum):
    """Valid sources for prospect acquisition."""
    TRADE_SHOW = "trade_show"
    RIDE_ALONG = "ride_along"
    PROSPECTION = "prospection"
    RECOMMENDATION = "recommendation"
    OTHER = "other"

class ProspectStatus(str, Enum):
    """
    Prospect status in the workflow.

    - NEW : Just imported, not yet contacted.
    - CONTACTED : Email sequence started
    - RESPONDED : Prospect replied to email
    - ARCHIVED : Moved to CRM or Sleepy Customer Base
    """
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    ARCHIVED = "archived"

class Prospect(Base, TimestampMixin):
    """
    Prospect/ Lead from one of our souces. 
    
    Prospects enter the system via:
    1. Trade Show (CSV import)
    2. Ride Along (web form)
    3. Prospection (web form)
    4. Recommendation (web form)

    They are then processed through the email automation workflow.

    Attributes:
        email: unique Email address (primary identifier)
        source: Origin of the prospect (trade_show, ride_along, etc.)
        status: Current position in workflow (new, contacted, responded, archived)
    """

    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)

    # Personal information
    first_name = Column(String(100), nullable=False, comment="First name")
    last_name = Column(String(100), nullable=False, comment="Last name")
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Email address (unique identifier)"
    )
    phone_number = Column(String(20), nullable=True, comment="Phone number")
    position = Column(String(100), nullable=True, comment="Job title")

    # Company information
    company_name = Column(String(255), nullable=True, comment="Company name")
    company_size = Column(
        String(50),
        nullable=True,
        comment="Company size (e.g., 1-10, 11-50, 51-200, etc.)"
    )
    market = Column(String(100), nullable=True)

    # Source tracking
    source = Column(
        SqlEnum(ProspectSource),
        nullable=False,
        index=True,
        comment="Origin of the prospect"
    )
    source_notes = Column(
        Text,
        nullable=True,
        comment="Additional context from source"
    ) 

    # Workflow status
    status = Column(
        SqlEnum(ProspectStatus),
        nullable=False,
        index=True,
        default=ProspectStatus.NEW,
        comment="Current workflow status"
    )

    # Relationships
    product_interests = relationship(
        "ProspectProduct",
        back_populates="prospect",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prospect(id={self.id}, email='{self.email}', status='{self.status.value}')>"
    
    @property
    def full_name(self) -> str:
        """Returns the full name of the prospect."""
        return f"{self.first_name} {self.last_name}"