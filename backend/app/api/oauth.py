"""
SPINE V1 — api/oauth.py
==========================
Rôle : Endpoints OAuth pour connecter Gmail et Outlook.
Dépendances : app.services.oauth, app.models.oauth_state, app.services.crypto
Utilisé par : frontend/Settings, app.main
Sécurité : - State tokens stockés en DB avec TTL 5 min (anti-CSRF)
           - Tokens OAuth chiffrés AES-256 Fernet avant persistance
           - Nettoyage automatique des states expirés à chaque appel
Dernière modification : 2026-05-25 — migration oauth_states dict → table DB + chiffrement tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from app.db import get_db
from app.models.user import User
from app.models.oauth_state import OAuthState
from app.services.oauth.gmail_oauth import (
    get_gmail_auth_url,
    exchange_code_for_tokens as exchange_gmail_code,
    get_gmail_user_info,
)
from app.services.oauth.outlook_oauth import (
    get_outlook_auth_url,
    exchange_code_for_tokens as exchange_outlook_code,
    get_outlook_user_info,
)
from app.services.crypto import encrypt
from app.api.deps import get_current_user

router = APIRouter(tags=["oauth"])

STATE_TTL_MINUTES = 5


def _cleanup_expired_states(db: Session) -> None:
    """Supprime les states OAuth expirés. Appelé à chaque connect pour éviter l'accumulation."""
    db.query(OAuthState).filter(OAuthState.expires_at < datetime.utcnow()).delete()
    db.commit()


@router.get("/gmail/connect")
async def connect_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initie le flow OAuth Gmail. Retourne l'URL d'autorisation Google."""
    _cleanup_expired_states(db)

    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        state=state,
        user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=STATE_TTL_MINUTES)
    )
    db.add(oauth_state)
    db.commit()

    auth_url = get_gmail_auth_url(state)
    return {"auth_url": auth_url}


@router.get("/gmail/callback")
async def gmail_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """Callback Gmail OAuth. Échange le code contre des tokens et les stocke chiffrés."""
    # Vérifie et consomme le state (le supprime immédiatement — usage unique)
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.expires_at > datetime.utcnow()
    ).first()

    if not oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state token")

    user_id = oauth_state.user_id
    db.delete(oauth_state)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        tokens = exchange_gmail_code(code)
        user_info = get_gmail_user_info(tokens["access_token"])

        user.gmail_connected = True
        user.gmail_email = user_info["email"]
        user.gmail_access_token = encrypt(tokens["access_token"])
        user.gmail_refresh_token = encrypt(tokens.get("refresh_token", ""))

        if not user.default_email_provider:
            user.default_email_provider = "gmail"

        db.commit()
        return RedirectResponse(url="http://localhost:5173/settings?oauth=gmail&status=success")

    except Exception as e:
        return RedirectResponse(url=f"http://localhost:5173/settings?oauth=gmail&status=error&message={str(e)}")


@router.get("/outlook/connect")
async def connect_outlook(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initie le flow OAuth Outlook. Retourne l'URL d'autorisation Microsoft."""
    _cleanup_expired_states(db)

    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        state=state,
        user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=STATE_TTL_MINUTES)
    )
    db.add(oauth_state)
    db.commit()

    auth_url = get_outlook_auth_url(state)
    return {"auth_url": auth_url}


@router.get("/outlook/callback")
async def outlook_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """Callback Outlook OAuth. Échange le code contre des tokens et les stocke chiffrés."""
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.expires_at > datetime.utcnow()
    ).first()

    if not oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state token")

    user_id = oauth_state.user_id
    db.delete(oauth_state)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        tokens = exchange_outlook_code(code)
        user_info = get_outlook_user_info(tokens["access_token"])

        user.outlook_connected = True
        user.outlook_email = user_info["email"]
        user.outlook_access_token = encrypt(tokens["access_token"])
        user.outlook_refresh_token = encrypt(tokens.get("refresh_token", ""))

        if not user.default_email_provider:
            user.default_email_provider = "outlook"

        db.commit()
        return RedirectResponse(url="http://localhost:5173/settings?oauth=outlook&status=success")

    except Exception as e:
        return RedirectResponse(url=f"http://localhost:5173/settings?oauth=outlook&status=error&message={str(e)}")


@router.post("/disconnect/{provider}")
async def disconnect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Déconnecte un provider OAuth et efface ses tokens."""
    if provider not in ["gmail", "outlook"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider")

    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if provider == "gmail":
        db_user.gmail_connected = False
        db_user.gmail_email = None
        db_user.gmail_access_token = None
        db_user.gmail_refresh_token = None
        if db_user.default_email_provider == "gmail":
            db_user.default_email_provider = "outlook" if db_user.outlook_connected else None

    elif provider == "outlook":
        db_user.outlook_connected = False
        db_user.outlook_email = None
        db_user.outlook_access_token = None
        db_user.outlook_refresh_token = None
        if db_user.default_email_provider == "outlook":
            db_user.default_email_provider = "gmail" if db_user.gmail_connected else None

    db.commit()
    return {"message": f"{provider.capitalize()} disconnected successfully"}


@router.get("/status")
async def oauth_status(
    current_user: User = Depends(get_current_user),
):
    """Retourne le statut de connexion OAuth du user courant."""
    return {
        "gmail": {
            "connected": current_user.gmail_connected,
            "email": current_user.gmail_email,
        },
        "outlook": {
            "connected": current_user.outlook_connected,
            "email": current_user.outlook_email,
        },
        "default_provider": current_user.default_email_provider,
    }