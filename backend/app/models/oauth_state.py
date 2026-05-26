"""
SPINE V1 - oauth_state model
==========================
Rôle : Stocke les state tokens OAuth en base avec TTL en 5 minutes. 
Remplace le dict en mémoire (oauth_states = {}) qui ne survivait pas aux redémarrages et cassé en multi-worker.
Dépendances : app.models.base
Utilisé par : app.api.oauth (pour stocker et valider les state tokens)
Sécurité : Le stat est un token aléatoire de 32 bytes (secrets.token_urlsafe)/
expries_at empêche la réutilisation après 5 minutes. 
Nettoyage automatique des états expirés à chaque appel Oauth.
Dernière modification : 2026-05-25 — création du modèle
"""

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta

from app.models.base import Base

class OAuthState(Base):
    """
    State token temporaire pour le flow Oauth.

    Le flow Oauth fonctionne en 2 étapes :
    1. /connect -> génère un state, redirgie vers Google/Microsoft
    2. /callback -> vérifie le state, échange le code contre les tokens

    Le state sert à prévenir les attaques CSRF : sans lui, n'importe qui
    pourrait forger un callback et connecter son compte OAuth à un autre user.
    """
    __tablename__ = "oauth_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)