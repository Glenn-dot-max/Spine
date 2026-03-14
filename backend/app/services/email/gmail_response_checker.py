"""
Gmail response checker - detects replies from prospects.
"""
from typing import Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


def check_gmail_thread_for_response(
    user: User,
    db: Session,
    thread_id: str,
    prospect_email: str
) -> Dict:
    """
    Check if a prospect has replied in a Gmail thread.
    
    Args:
        user: User with Gmail connected
        db: Database session
        thread_id: Gmail thread ID to check
        prospect_email: Prospect's email to detect their replies
    
    Returns:
        Dict with:
            - has_response: bool
            - response_content: str (first 1000 chars)
            - response_date: datetime
    """
    # Build credentials
    credentials = Credentials(
        token=user.gmail_access_token,
        refresh_token=user.gmail_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
        ]
    )
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        user.gmail_access_token = credentials.token
        db.commit()
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        # Get the thread
        thread = service.users().threads().get(
            userId='me',
            id=thread_id,
            format='full'
        ).execute()
        
        # Check each message in thread
        messages = thread.get('messages', [])
        
        # Skip first message (our sent email)
        if len(messages) <= 1:
            return {
                "has_response": False,
                "response_content": None,
                "response_date": None
            }
        
        # Check messages after our initial email
        for message in messages[1:]:  # Skip first message
            headers = message.get('payload', {}).get('headers', [])
            
            # Get sender (From header)
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            
            # Check if sender is the prospect
            if prospect_email.lower() in from_header.lower():
                # Found a response!
                
                # Extract message body
                body = _extract_message_body(message)
                
                # Get date
                date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
                
                return {
                    "has_response": True,
                    "response_content": body,
                    "response_date": date_header
                }
        
        # No response found
        return {
            "has_response": False,
            "response_content": None,
            "response_date": None
        }
        
    except Exception as e:
        raise Exception(f"Failed to check Gmail thread: {str(e)}")


def _extract_message_body(message: Dict) -> str:
    """
    Extract text body from Gmail message.
    """
    payload = message.get('payload', {})
    
    # Try to get body from parts
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    import base64
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Try HTML if no plain text
            if part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    import base64
                    return base64.urlsafe_b64decode(data).decode('utf-8')
    
    # Single part message
    if 'body' in payload:
        data = payload['body'].get('data', '')
        if data:
            import base64
            return base64.urlsafe_b64decode(data).decode('utf-8')
    
    return ""
