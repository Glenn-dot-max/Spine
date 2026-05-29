"""
Outlook response checker - detects replies from prospects.
"""
from typing import Dict
import base64
import json
import requests
from urllib.parse import quote
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.oauth.outlook_oauth import refresh_outlook_token
from app.services.crypto import decrypt, encrypt


def _refresh_outlook_access_token(user: User, db: Session) -> str:
    """Refresh the user's Outlook access token and persist it to the DB."""
    refresh_token = decrypt(user.outlook_refresh_token)
    tokens = refresh_outlook_token(refresh_token)

    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise Exception("User not found")
    
    db_user.outlook_access_token = encrypt(tokens["access_token"])
    if tokens.get("refresh_token"):
        db_user.outlook_refresh_token = encrypt(tokens["refresh_token"])

    db.commit()
    db.refresh(db_user)

    return tokens["access_token"]

def check_outlook_conversation_for_response(
    user: User,
    db: Session,
    conversation_id: str,
    prospect_email: str
) -> Dict:
    """
    Check if a prospect has replied in an Outlook conversation.
    
    Args:
        user: User with Outlook connected
        db: Database session
        conversation_id: Outlook conversation ID
        prospect_email: Prospect's email
    
    Returns:
        Dict with has_response, response_content, response_date
    """
    # Get access token (decrypt before use)
    access_token = decrypt(user.outlook_access_token)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Note: $orderby cannot be combined with $filter on /me/messages (Graph API limitation)
        encoded_id = quote(conversation_id, safe='')
        url = (
            f"https://graph.microsoft.com/v1.0/me/messages"
            f"?$filter=conversationId eq '{encoded_id}'"
            f"&$top=50"
        )
        response = requests.get(url, headers=headers)

        # Handle token expiration by refreshing and retrying once
        if response.status_code == 401:
            access_token = _refresh_outlook_access_token(user, db)
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
        
        response.raise_for_status()
        messages = response.json().get('value', [])
        
        # Sort by date client-side
        messages.sort(key=lambda x: x.get("receivedDateTime", ""), reverse=True)
        
        # Check for responses from prospect
        for message in messages:
        
            sender = message.get('from', {}).get('emailAddress', {}).get('address', '')
            
            if sender.lower() == prospect_email.lower():
                # Found response!
                body = message.get('body', {}).get('content', '')
                received_date = message.get('receivedDateTime')
                
                return {
                    "has_response": True,
                    "response_content": body,
                    "response_date": received_date
                }
        
        # No response found
        return {
            "has_response": False,
            "response_content": None,
            "response_date": None
        }
        
    except Exception as e:
        raise Exception(f"Failed to check Outlook conversation: {str(e)}")

