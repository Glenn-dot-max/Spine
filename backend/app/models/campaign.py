"""
SPINE V1 - campaign model
==========================
Rôle: Modèle SQLAlchemy pour les campagnes.
Dépendances: app.models.base
Utilisé par: routes/campaigns.py, routes/campaign_emails.py
Sécurité: user_id obligatoire sur toutes les requêtes API
Dernière modification : 2026 - 06 - 03 - ajout CampaignSource + champs builder V1
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum, Boolean
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

class CampaignSource(str, enum.Enum):
    """Source of the campaign."""
    trade_show = "trade_show"
    ride_along = "ride_along"
    outreach = "outreach"

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Core
    name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    distributor_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TradeShowStatus), nullable=False, default=TradeShowStatus.UPCOMING)

    # Source simplifiée
    campaign_source = Column(Enum(CampaignSource), default=CampaignSource.trade_show, nullable=False)

    # Contexte distributeur
    is_distributor_show = Column(Boolean, default=False, nullable=False)
    distributor_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    auto_cc_sales_rep = Column(Boolean, default=False, nullable=False)

    # Blocs de contenu
    company_intro_text = Column(Text, nullable=True)
    catalog_pitch_text = Column(Text, nullable=True)

    offer_samples = Column(Boolean, default=False, nullable=False)
    samples_note = Column(Text, nullable=True)

    segment_note_global = Column(Text, nullable=True)
    segment_note_restaurant = Column(Text, nullable=True)
    segment_note_industry = Column(Text, nullable=True)
    segment_note_retail = Column(Text, nullable=True)

    # Séqunce d'emails
    followup_delay_1 = Column(Integer, default=7, nullable=True)
    followup_delay_2 = Column(Integer, default=14, nullable=True)
    followup_delay_3 = Column(Integer, default=21, nullable=True)

    # Templates campagne
    template_initial_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    template_followup_1_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    template_followup_2_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    template_followup_3_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)

    attachment_paths = Column(Text, nullable=True)  # JSON list of attachment file paths
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="campaigns")
    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")
    products = relationship("CampaignProduct", back_populates="campaign", cascade="all, delete-orphan")
    distributor_company = relationship("Company", foreign_keys=[distributor_company_id])

class CampaignContact(Base):
    __tablename__ = "campaign_contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False, index=True)

    status = Column(String(50), nullable=False, default="pending") 
    notes = Column(Text, nullable=True)

    email_sequence_step = Column(Integer, default=0, nullable=False) 
    last_email_sent_at = Column(DateTime, nullable=True)
    email_thread_id = Column(String(255), nullable=True)
    email_message_id = Column(String(255), nullable=True)

    response_received_at = Column(DateTime, nullable=True)
    last_response_content = Column(String, nullable=True)

    next_follow_up_scheduled_at = Column(DateTime, nullable=True)

    custom_followup_delay_1 = Column(Integer, nullable=True)
    custom_followup_delay_2 = Column(Integer, nullable=True)
    custom_followup_delay_3 = Column(Integer, nullable=True)

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