"""
Gmail OAuth helper.
"""
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
]

def get_gmail_auth_url(state: str) -> str:
  """Generate Gmail OAuth authorization URL."""
  flow = Flow.from_client_config(
    {
      "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
      }
    },
    scopes=SCOPES,
    redirect_uri=GOOGLE_REDIRECT_URI,
  )

  authorization_url, _ = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true',
    state=state,
    prompt='consent',
  )

  return authorization_url

def exchange_code_for_tokens(code: str) -> dict:
  """Exchange authorization code for access and refresh tokens."""
  flow = Flow.from_client_config(
    {
      "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
      }
    },
    scopes=SCOPES,
    redirect_uri=GOOGLE_REDIRECT_URI,
  )

  flow.fetch_token(code=code)
  credentials = flow.credentials

  return {
    "access_token": credentials.token,
    "refresh_token": credentials.refresh_token,
    "token_uri": credentials.token_uri,
    "client_id": credentials.client_id,
    "client_secret": credentials.client_secret,
    "scopes": credentials.scopes,
  }

def get_gmail_user_info(access_token: str) -> dict:
  """Get Gmail user info (email address)."""
  credentials = Credentials(token=access_token)
  service = build('oauth2', 'v2', credentials=credentials)
  user_info = service.userinfo().get().execute()
  
  return {
    "email": user_info.get("email"),
    "verified_email": user_info.get("verified_email"),
  }

def refresh_gmail_token(refresh_token: str) -> str:
  """Refresh Gmail access token."""
  credentials = Credentials(
    token=None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
  )

  from google.auth.transport.requests import Request
  credentials.refresh(Request())

  return credentials.token