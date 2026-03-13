"""
Outlook email sender using OAuth tokens.
Sends emails via Microsoft Graph API and handles token refresh.
"""
import requests
import msal
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.config import (
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    MICROSOFT_TENANT_ID,
)


class OutlookSender:
    """
    Sends emails via Microsoft Graph API using user's OAuth tokens.
    """
    
    def __init__(self, user: User, db: Session):
        """
        Initialize Outlook sender for a specific user.
        
        Args:
            user: User object with Outlook OAuth tokens
            db: Database session (to save refreshed tokens)
        """
        self.user = user
        self.db = db
        
        # Verify user has Outlook connected
        if not user.outlook_connected:
            raise ValueError("User does not have Outlook connected")
        
        if not user.outlook_access_token:
            raise ValueError("User does not have Outlook access token")
    
    def _refresh_token_if_needed(self) -> str:
        """
        Refresh Outlook access token if needed.
        
        Returns:
            Valid access token
        """
        # Try to use current token first
        # If it fails, we'll catch and refresh
        
        # For now, we'll just return current token
        # Microsoft tokens last 1 hour, we refresh on error
        return self.user.outlook_access_token
    
    def _refresh_access_token(self) -> str:
        """
        Force refresh the Outlook access token.
        
        Returns:
            New access token
        """
        authority = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}"
        
        app = msal.ConfidentialClientApplication(
            MICROSOFT_CLIENT_ID,
            authority=authority,
            client_credential=MICROSOFT_CLIENT_SECRET,
        )
        
        result = app.acquire_token_by_refresh_token(
            self.user.outlook_refresh_token,
            scopes=[
                "https://graph.microsoft.com/Mail.Send",
                "https://graph.microsoft.com/Mail.Read",
            ]
        )
        
        if "error" in result:
            raise Exception(f"Token refresh failed: {result.get('error_description')}")
        
        # Save new token to database
        new_token = result["access_token"]
        self.user.outlook_access_token = new_token
        self.db.commit()
        
        return new_token
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        reply_to_message_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Send an email via Microsoft Graph API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            reply_to_message_id: Message ID to reply to (for threading)
            conversation_id: Conversation ID (for threading)
        
        Returns:
            Dictionary with:
                - message_id: Outlook message ID
                - conversation_id: Outlook conversation ID (thread)
        
        Raises:
            Exception: If sending fails
        """
        try:
            # Get access token
            access_token = self._refresh_token_if_needed()
            
            # Prepare Graph API request
            url = "https://graph.microsoft.com/v1.0/me/sendMail"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Build email payload (Microsoft Graph format)
            email_payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": html_body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                },
                "saveToSentItems": True
            }
            
            # Add threading headers if this is a reply
            if reply_to_message_id:
                # Microsoft uses different approach for threading
                # We need to reply to the original message
                url = f"https://graph.microsoft.com/v1.0/me/messages/{reply_to_message_id}/reply"
                # Simplified payload for reply
                email_payload = {
                    "message": {
                        "body": {
                            "contentType": "HTML",
                            "content": html_body
                        }
                    }
                }
            
            # Send the email
            response = requests.post(url, headers=headers, json=email_payload)
            
            # Handle token expiration
            if response.status_code == 401:
                # Token expired, refresh and retry
                access_token = self._refresh_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
                response = requests.post(url, headers=headers, json=email_payload)
            
            # Check for errors
            response.raise_for_status()
            
            # For replies, Microsoft doesn't return message details
            # For new messages, we get the sent message
            if reply_to_message_id:
                return {
                    "message_id": reply_to_message_id,  # Use original message ID
                    "conversation_id": conversation_id or reply_to_message_id
                }
            else:
                # Get the sent message details
                # Microsoft Graph sendMail doesn't return message ID directly
                # We need to query sent items to get it
                # For now, return empty - will be filled by next email
                return {
                    "message_id": "",  # Will be updated on next send
                    "conversation_id": ""
                }
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response else str(e)
            raise Exception(f"Outlook API error: {error_detail}")
        except Exception as e:
            raise Exception(f"Failed to send email via Outlook: {str(e)}")


def send_email_via_outlook(
    user: User,
    db: Session,
    to_email: str,
    subject: str,
    html_body: str,
    reply_to_message_id: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Convenience function to send email via Outlook.
    
    Args:
        user: User with Outlook OAuth connected
        db: Database session
        to_email: Recipient
        subject: Subject line
        html_body: HTML email content
        reply_to_message_id: For threading (optional)
        conversation_id: For threading (optional)
    
    Returns:
        Dict with message_id and conversation_id
    """
    sender = OutlookSender(user, db)
    return sender.send_email(to_email, subject, html_body, reply_to_message_id, conversation_id)