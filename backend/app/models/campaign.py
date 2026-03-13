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
    UPCOMING = "upcoming"       # À venir
    ACTIVE = "active"           # En cours
    COMPLETED = "completed"     # Terminé
    ARCHIVED = "archived"       # Archivé


class Campaign(Base):
    """
    Campaign represents a trade show or professional exhibition.
    Groups prospects (leads collected at the show) and products (displayed on booth).
    """
    __tablename__ = "campaigns"
    
    # Identifiants
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Informations trade show
    name = Column(String(255), nullable=False)              # "Show Chefs LA 2026"
    event_date = Column(Date, nullable=False)               # Date de début du salon
    end_date = Column(Date, nullable=True)                  # Date de fin (salons durent 2-5 jours)
    location = Column(String(255), nullable=True)           # "Los Angeles Convention Center"
    
    # Salon distributeur (null si salon direct B2B)
    distributor_name = Column(String(255), nullable=True)   # "US Foods", "Sysco", null si direct
    
    description = Column(Text, nullable=True)               # Notes générales sur le salon
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
    Tracks which prospects were met at which show and manages email sequences.
    """
    __tablename__ = "campaign_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False, index=True)
    
    # Status du contact dans cette campagne
    # pending = pas encore contacté post-salon
    # contacted = email/appel fait
    # responded = a répondu
    # meeting_scheduled = RDV planifié
    # converted = a acheté
    status = Column(String(50), default="pending", nullable=False)
    
    # Notes spécifiques à ce salon
    # Ex: "Came to booth twice, very interested in knife series"
    notes = Column(Text, nullable=True)
    
    # ========== CHAMPS POUR SÉQUENCE D'EMAILS ==========
    
    # Étape dans la séquence d'emails
    # 0 = email initial pas encore envoyé
    # 1 = email initial envoyé
    # 2 = relance 1 envoyée
    # 3 = relance 2 envoyée
    # 4 = relance 3 envoyée
    email_sequence_step = Column(Integer, default=0, nullable=False)
    
    # Date du dernier email envoyé à ce contact
    last_email_sent_at = Column(DateTime, nullable=True)
    
    # ID du thread email (pour threading Gmail/Outlook)
    # Gmail format: "<CADsP...@mail.gmail.com>"
    # Outlook format: "AAMkADU3..."
    email_thread_id = Column(String(255), nullable=True)
    
    # Message ID du dernier email (pour Reply-To)
    email_message_id = Column(String(255), nullable=True)
    
    # ====================================================
    
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