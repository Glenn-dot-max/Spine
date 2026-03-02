"""
Outlook OAuth helper.
"""
import msal
import requests
from app.core.config import (
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    MICROSOFT_TENANT_ID,
    MICROSOFT_REDIRECT_URI,
)

SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/User.Read",
]

AUTHORITY = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}"


def get_outlook_auth_url(state: str) -> str:
    """Generate Outlook OAuth authorization URL."""
    app = msal.ConfidentialClientApplication(
        MICROSOFT_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=MICROSOFT_CLIENT_SECRET,
    )
    
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        state=state,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )
    
    return auth_url


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    app = msal.ConfidentialClientApplication(
        MICROSOFT_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=MICROSOFT_CLIENT_SECRET,
    )
    
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )
    
    if "error" in result:
        raise Exception(f"Error getting token: {result.get('error_description')}")
    
    return {
        "access_token": result.get("access_token"),
        "refresh_token": result.get("refresh_token"),
    }


def get_outlook_user_info(access_token: str) -> dict:
    """Get Outlook user info (email address)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers=headers,
    )
    response.raise_for_status()
    user_info = response.json()
    
    return {
        "email": user_info.get("mail") or user_info.get("userPrincipalName"),
    }


def refresh_outlook_token(refresh_token: str) -> str:
    """Refresh Outlook access token."""
    app = msal.ConfidentialClientApplication(
        MICROSOFT_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=MICROSOFT_CLIENT_SECRET,
    )
    
    result = app.acquire_token_by_refresh_token(
        refresh_token,
        scopes=SCOPES,
    )
    
    if "error" in result:
        raise Exception(f"Error refreshing token: {result.get('error_description')}")
    
    return result.get("access_token")