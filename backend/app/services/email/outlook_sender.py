"""
Outlook email sender using OAuth tokens.
Sends emails via Microsoft Graph API and handles token refresh.
"""
import base64
import json
import requests
from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.services.oauth.outlook_oauth import refresh_outlook_token

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
    
    def _is_token_expired(self, token: str) -> bool:
        """
        Check if a JWT access token is expired by decoding its payload.

        Returns:
            True if expired or unreadable, False if still valid.
        """
        try:
            # JWT is three base64url-encoded parts separated by dots
            payload_b64 = token.split('.')[1]
            # Add padding so base64 can decode it
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_b64))
            exp = decoded.get("exp", 0)
            return datetime.now(timezone.utc).timestamp() >= exp
        except Exception:
            # If we can't decode, assume expired to trigger a refresh
            return True

    def _refresh_token_if_needed(self) -> str:
        """
        Return a valid access token, refreshing proactively if the current one is expired.

        Returns:
            Valid access token
        """
        print("🔍 [DEBUG] Checking if token is expired...")
        is_expired = self._is_token_expired(self.user.outlook_access_token)
        print(f"🔍 [DEBUG] Token expired: {is_expired}")
        
        if is_expired:
            print("🔄 [DEBUG] Refreshing token...")
            return self._refresh_access_token()
        
        print("✅ [DEBUG] Token still valid")
        return self.user.outlook_access_token
        
    
    def _refresh_access_token(self) -> str:
        """
        Force refresh the Outlook access token using the stored refresh token.
        Saves both the new access token and the new refresh token (if returned) to the DB.

        Returns:
            New access token
        """
        try:
            print("🔄 [DEBUG] Calling refresh_outlook_token...")
            tokens = refresh_outlook_token(self.user.outlook_refresh_token)
            print("✅ [DEBUG] Got new tokens")

            # ✅ Refetch user from DB to attach to session
            from app.models.user import User
            print("🔍 [DEBUG] Fetching user from DB...")
            db_user = self.db.query(User).filter(User.id == self.user.id).first()
            if not db_user:
                raise Exception("User not found")
            
            print("💾 [DEBUG] Saving new tokens to DB...")
            db_user.outlook_access_token = tokens["access_token"]
            # MSAL may issue a new refresh token; save it if provided
            if tokens.get("refresh_token"):
                db_user.outlook_refresh_token = tokens["refresh_token"]

            self.db.commit()
            self.db.refresh(db_user)
            print("✅ [DEBUG] Tokens saved to DB")

            # Update instance variable
            self.user = db_user

            return tokens["access_token"]

        except Exception as e:
            print(f"❌ [DEBUG] Refresh failed: {str(e)}")
            raise Exception(f"Failed to refresh Outlook token: {str(e)}")


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
            print("📧 [DEBUG] Starting send_email...")
            # Get access token
            access_token = self._refresh_token_if_needed()
            print(f"🔑 [DEBUG] Got access token (length: {len(access_token)})")
            
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
            print(f"📤 [DEBUG] Sending POST to {url}")
            response = requests.post(url, headers=headers, json=email_payload)
            print(f"📥 [DEBUG] Response status: {response.status_code}")
            
            # Handle token expiration
            if response.status_code == 401:
                print("🔄 [DEBUG] Got 401, forcing refresh and retry...")
                # Token expired, refresh and retry
                access_token = self._refresh_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
                response = requests.post(url, headers=headers, json=email_payload)
                print(f"📥 [DEBUG] Retry response status: {response.status_code}")
            
            # Check for errors
            response.raise_for_status()
            
            print("✅ [DEBUG] Email sent successfully!")
            
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
            error_body = ""
            try:
                error_body = e.response.json()
            except Exception:
                error_body = str(e)
            status_code = e.response.status_code if e.response is not None else "unknown"
            print(f"❌ [DEBUG] HTTP Error: {status_code} - {error_body}")
            raise Exception(f"Outlook API error: {status_code} - {error_body}")
        except Exception as e:
            print(f"❌ [DEBUG] Exception: {str(e)}")
            raise Exception(f"Failed to send email via Outlook: {str(e)}") from e


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
