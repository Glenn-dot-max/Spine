"""
Campaign model for tracking trade show leads.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base

class TradeShowStatus(str, enum.Enum):
    """Status of a trade show campaign."""
    UPCOMING = "upcoming"       
    ACTIVE = "active"           
    COMPLETED = "completed"     
    ARCHIVED = "archived"       

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    distributor_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TradeShowStatus), default=TradeShowStatus.UPCOMING, nullable=False)

    # ========== CHAMPS POUR SÉQUENCE D'EMAILS ==========
    followup_delay_1 = Column(Integer, default=7, nullable=False)
    followup_delay_2 = Column(Integer, default=14, nullable=False)
    followup_delay_3 = Column(Integer, default=21, nullable=False)
    # ====================================================

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="campaigns")
    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")
    products = relationship("CampaignProduct", back_populates="campaign", cascade="all, delete-orphan")

class CampaignContact(Base):
    __tablename__ = "campaign_contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False, index=True)

    status = Column(String(50), default="pending", nullable=False)
    notes = Column(Text, nullable=True)

    email_sequence_step = Column(Integer, default=0, nullable=False)
    last_email_sent_at = Column(DateTime, nullable=True)
    email_thread_id = Column(String(255), nullable=True)
    email_message_id = Column(String(255), nullable=True)

    response_received_at = Column(DateTime, nullable=True)
    last_response_content = Column(String, nullable=True)

    next_follow_up_scheduled_at = Column(DateTime, nullable=True)

    # ============== DÉLAI CUSTOMISÉ DE RELANCE ==============
    custom_followup_delay_1 = Column(Integer, nullable=True)
    custom_followup_delay_2 = Column(Integer, nullable=True)
    custom_followup_delay_3 = Column(Integer, nullable=True)
    # ====================================================

    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    campaign = relationship("Campaign", back_populates="contacts")
    prospect = relationship("Prospect")

class CampaignProduct(Base):
    __tablename__ = "campaign_products"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    campaign = relationship("Campaign", back_populates="products")
    product = relationship("Product")
