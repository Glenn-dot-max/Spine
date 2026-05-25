"""
SPINE V1 - prospect model
==========================
Rôle: Modèle SQLAlchemy pour les prospects/leads dans le CRM.
Dépendances: app.models.base, app.models.company
Utilisé par: routes/prospects.py, services/email/email_service.py, routes/campaigns.py
Sécurité: Unique Constraint sur (email, user_id) - multi-tenant safe. user_id obligatoire sur toutes les requêtes.
A faire : ajouter status oven/fridge/trash/converted (tâche 8)
Denière modificaton : 2026 - 05 - 2025 - UniqueConstraint email+user_id (fix multi-tenant) 
"""
from sqlalchemy import String, Text, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
import enum

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company

class ProspectSource(str, enum.Enum):
    """Source of prospect acquisition."""
    trade_show = "trade_show"
    ride_along = "ride_along"
    referral = "referral"
    cold_outreach = "cold_outreach"
    inbound = "inbound"
    other = "other"

class ProspectStatus(str, enum.Enum):
    """Current status of the prospect."""
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    proposal_sent = "proposal_sent"
    negociation = "negotiation"
    closed_won = "closed_won"
    closed_lost = "closed_lost"

class Prospect(Base, TimestampMixin):
    """Prospect/lead for CRM management."""
    __tablename__ = "prospects"

    __table_args__ = (
        UniqueConstraint('email', 'user_id', name='uq_prospects_email_user'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Owner 
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Contact information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))

    # Company information
    position: Mapped[Optional[str]] = mapped_column(String(100))
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    company_id : Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    company_size: Mapped[Optional[str]] = mapped_column(String(50))
    market: Mapped[Optional[str]] = mapped_column(String(100))

    # Lead Management
    source: Mapped[ProspectSource] = mapped_column(Enum(ProspectSource), nullable=False)
    source_notes: Mapped[Optional[str]] = mapped_column(Text)
    source_detail: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[ProspectStatus] = mapped_column(
        Enum(ProspectStatus),
        nullable=False,
        default=ProspectStatus.new
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="prospects")
    product_interests: Mapped[List["ProspectProduct"]] = relationship(
        back_populates="prospect",
        cascade="all, delete-orphan"
    )
    company: Mapped[Optional["Company"]] = relationship(back_populates="prospects")
    # Indexes for performance
    __table_args__ = (
        Index('ix_prospects_user_status', 'user_id', 'status'),
        Index('ix_prospects_user_source', 'user_id', 'source'),
    )

    def __repr__(self) -> str:
        return f"<Prospect {self.first_name} {self.last_name} ({self.email}) - Status: {self.status}>"

    
