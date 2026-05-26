"""
SPINE V1 — migrate_encrypt_tokens
==================================
Rôle : Script one-shot pour chiffrer les tokens OAuth existants en base.
       À exécuter UNE SEULE FOIS après le déploiement du chiffrement Fernet.
Dépendances : app.db, app.models.user, app.services.crypto
Sécurité : Ne logge aucun token. Affiche uniquement les emails et statuts.
À faire : Supprimer ce script après exécution confirmée.
Dernière modification : 2026-05-25 — création
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models.user import User
from app.services.crypto import encrypt

def is_already_encrypted(value: str) -> bool:
    """
    Un token Fernet commence toujours par 'gAAAAA'.
    Un token OAuth (JWT ou opaque) ne commence jamais par ça.
    Cette fonction évite de double-chiffrer si le script tourne deux fois.
    """
    return value.startswith("gAAAAA")

def migrate():
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            (User.gmail_access_token != None) | (User.outlook_access_token != None)
        ).all()

        print(f"🔍 {len(users)} user(s) à migrer\n")

        for user in users:
            print(f"→ {user.email}")
            changed = False

            # Gmail
            if user.gmail_access_token and not is_already_encrypted(user.gmail_access_token):
                user.gmail_access_token = encrypt(user.gmail_access_token)
                print("  ✅ gmail_access_token chiffré")
                changed = True

            if user.gmail_refresh_token and not is_already_encrypted(user.gmail_refresh_token):
                user.gmail_refresh_token = encrypt(user.gmail_refresh_token)
                print("  ✅ gmail_refresh_token chiffré")
                changed = True

            # Outlook
            if user.outlook_access_token and not is_already_encrypted(user.outlook_access_token):
                user.outlook_access_token = encrypt(user.outlook_access_token)
                print("  ✅ outlook_access_token chiffré")
                changed = True

            if user.outlook_refresh_token and not is_already_encrypted(user.outlook_refresh_token):
                user.outlook_refresh_token = encrypt(user.outlook_refresh_token)
                print("  ✅ outlook_refresh_token chiffré")
                changed = True

            if not changed:
                print("  ⏭️  déjà chiffré, rien à faire")

        db.commit()
        print("\n✅ Migration terminée.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur : {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()