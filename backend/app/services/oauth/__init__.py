"""
OAuth services.
"""
from .gmail_oauth import (
    get_gmail_auth_url,
    exchange_code_for_tokens as exchange_gmail_code,
    get_gmail_user_info,
    refresh_gmail_token,
)
from .outlook_oauth import (
    get_outlook_auth_url,
    exchange_code_for_tokens as exchange_outlook_code,
    get_outlook_user_info,
    refresh_outlook_token,
)

__all__ = [
    "get_gmail_auth_url",
    "exchange_gmail_code",
    "get_gmail_user_info",
    "refresh_gmail_token",
    "get_outlook_auth_url",
    "exchange_outlook_code",
    "get_outlook_user_info",
    "refresh_outlook_token",
]