"""
Outlook response checker - detects replies from prospects.
"""
from typing import Dict
import requests
from sqlalchemy.orm import Session

from app.models.user import User


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
    # Get access token (refresh if needed)
    access_token = user.outlook_access_token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get messages in conversation
        url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=conversationId eq '{conversation_id}'&$orderby=receivedDateTime desc"
        response = requests.get(url, headers=headers)
        
        # Handle token expiration
        if response.status_code == 401:
            # Refresh token logic here
            pass
        
        response.raise_for_status()
        messages = response.json().get('value', [])
        
        # Check for responses from prospect
        for message in messages[1:]:  # Skip first (our email)
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

