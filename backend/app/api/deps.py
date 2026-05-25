"""
SPINE V1 - api/deps.py
==========================
Rôle : Point de compatibilité - réexporte depuis app.core.deps.
Dépendances : app.core.deps
Utilisé par : tous les routes /* et api/oauth.py
Sécurité : La logique réelle est dans app.core.deps (validation token type + is_active)
À faire : migrer tous les imports vers app.core.deps directetement (nettoyage futur)
Dernière modification : 2026 - 05 - 2025 - suppression du code JWT dupliqué
"""

from app.core.deps import (
    get_current_user,
    get_db
)

__all__ = [
    "get_current_user",
    "get_db"
]