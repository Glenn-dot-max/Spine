"""
OAuth endpoints for Gmail and Outlook.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import secrets

from app.db import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.oauth import (
    get_gmail_auth_url,
    exchange_gmail_code,
    get_gmail_user_info,
    get_outlook_auth_url,
    exchange_outlook_code,
    get_outlook_user_info,
)

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Store state tokens temporarily (in production, use Redis or database)
oauth_states = {}


@router.get("/gmail/connect")
async def connect_gmail(
    current_user: User = Depends(get_current_user),
):
    """
    Initiate Gmail OAuth flow.
    Returns the authorization URL to redirect the user to.
    """
    # Generate a random state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = current_user.id
    
    # Get Gmail authorization URL
    auth_url = get_gmail_auth_url(state)
    
    return {"auth_url": auth_url}


@router.get("/gmail/callback")
async def gmail_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Gmail OAuth callback.
    Exchanges the authorization code for tokens and stores them.
    """
    # Verify state token
    user_id = oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Exchange code for tokens
        tokens = exchange_gmail_code(code)
        
        # Get user info
        user_info = get_gmail_user_info(tokens["access_token"])
        
        # Update user in database
        user.gmail_connected = True
        user.gmail_email = user_info["email"]
        user.gmail_access_token = tokens["access_token"]
        user.gmail_refresh_token = tokens["refresh_token"]
        
        # Set as default provider if none set
        if not user.default_email_provider:
            user.default_email_provider = "gmail"
        
        db.commit()
        
        # Redirect to frontend success page
        return RedirectResponse(url="http://localhost:3000/settings?oauth=gmail&status=success")
        
    except Exception as e:
        # Redirect to frontend error page
        return RedirectResponse(url=f"http://localhost:3000/settings?oauth=gmail&status=error&message={str(e)}")


@router.get("/outlook/connect")
async def connect_outlook(
    current_user: User = Depends(get_current_user),
):
    """
    Initiate Outlook OAuth flow.
    Returns the authorization URL to redirect the user to.
    """
    # Generate a random state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = current_user.id
    
    # Get Outlook authorization URL
    auth_url = get_outlook_auth_url(state)
    
    return {"auth_url": auth_url}


@router.get("/outlook/callback")
async def outlook_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Outlook OAuth callback.
    Exchanges the authorization code for tokens and stores them.
    """
    # Verify state token
    user_id = oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Exchange code for tokens
        tokens = exchange_outlook_code(code)
        
        # Get user info
        user_info = get_outlook_user_info(tokens["access_token"])
        
        # Update user in database
        user.outlook_connected = True
        user.outlook_email = user_info["email"]
        user.outlook_access_token = tokens["access_token"]
        user.outlook_refresh_token = tokens["refresh_token"]
        
        # Set as default provider if none set
        if not user.default_email_provider:
            user.default_email_provider = "outlook"
        
        db.commit()
        
        # Redirect to frontend success page
        return RedirectResponse(url="http://localhost:3000/settings?oauth=outlook&status=success")
        
    except Exception as e:
        # Redirect to frontend error page
        return RedirectResponse(url=f"http://localhost:3000/settings?oauth=outlook&status=error&message={str(e)}")


@router.post("/disconnect/{provider}")
async def disconnect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect an email provider.
    """
    if provider not in ["gmail", "outlook"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider"
        )
    
    if provider == "gmail":
        current_user.gmail_connected = False
        current_user.gmail_email = None
        current_user.gmail_access_token = None
        current_user.gmail_refresh_token = None
        
        # Switch default provider if needed
        if current_user.default_email_provider == "gmail":
            current_user.default_email_provider = "outlook" if current_user.outlook_connected else None
    
    elif provider == "outlook":
        current_user.outlook_connected = False
        current_user.outlook_email = None
        current_user.outlook_access_token = None
        current_user.outlook_refresh_token = None
        
        # Switch default provider if needed
        if current_user.default_email_provider == "outlook":
            current_user.default_email_provider = "gmail" if current_user.gmail_connected else None
    
    db.commit()
    
    return {"message": f"{provider.capitalize()} disconnected successfully"}


@router.get("/status")
async def oauth_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get OAuth connection status for current user.
    """
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