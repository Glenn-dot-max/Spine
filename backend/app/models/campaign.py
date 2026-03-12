"""
Campaign model for tracking trade show leads.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base

class TradeShowStatus(str, enum.Enum):
    """Status of a trade show campaign."""
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Campaign(Base):
    """
    Campaign represents a trade show or pporfessional exhibition.
    Groups prospects (leads collected at the show) and products (displayed on booth).
    """
    __tablename__ = "campaigns"

    # Identifiants
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Informations trade show
    name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)

    # Salon distributeur
    distributor_name = Column(String(255), nullable=True)

    description = Column(Text, nullable=True)
    status = Column(Enum(TradeShowStatus), default=TradeShowStatus.UPCOMING, nullable=False)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    user = relationship("User", back_populates="campaigns")
    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")
    products = relationship("CampaignProduct", back_populates="campaign", cascade="all, delete-orphan")

class CampaignContact(Base):
    """
    Links prospects to trade show campaigns.
    Tracks which prospects were met at which campaign.
    """
    __tablename__ = "campaign_contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False, index=True)

    # Status du contact dans la campagne
    status = Column(String(50), default="pending", nullable=False)

    notes = Column(Text, nullable=True)

    # Métadonnées
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    campaign = relationship("Campaign", back_populates="contacts")
    prospect = relationship("Prospect")

class CampaignProduct(Base):
    """
    Links products to trade show campaigns.
    Tracks which products were displayed on the booth. 
    """

    __tablename__ = "campaign_products"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Métadonnées
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    campaign = relationship("Campaign", back_populates="products")
    product = relationship("Product")
