"""
SPINE V1 - crypto
==========================
Rôle : chiffrement/déchiffrement AES-256 Fernet pour les tokens OAuth.
Dépendances : app.core.config
Utilisé par : app.api.oauth
Sécurité : La FERNET_KEY ne doit pas apparaître dans les logs ni le code.
            Les rtokens déchiffrés ne vivent qu'en mémoire, jamais peristés en clair.
Dernière modification : 2026 - 05 - 2025 - création du module
"""

from cryptography.fernet import Fernet
from app.core.config import FERNET_KEY

_fernet = Fernet(FERNET_KEY.encode())

def encrypt(value: str) -> str:
    """Chiffre une chaine de caractères. Retourne la valeur chiffrée en string."""
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    """Déchiffre une chaine de caractères chiffrée. Retourne la valeur déchiffrée en string."""
    if not value:
        return value
    return _fernet.decrypt(value.encode()).decode()