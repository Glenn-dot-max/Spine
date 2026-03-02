"""
Application configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# JWT 
SECRET_KEY = os.getenv("SECRET_KEY", "s55n_EObC5I5zMl0nTfAsOTFUwgnMwTxS2OhNN00tFs")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spine_crm.db")

# Google Oauth (Gmail)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/oauth/gmail/callback")

# Microsoft Oauth (Outlook)
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/oauth/outlook/callback")
