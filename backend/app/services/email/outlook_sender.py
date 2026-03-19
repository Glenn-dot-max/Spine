"""
Outlook email sender using OAuth tokens.
Sends emails via Microsoft Graph API and handles token refresh.
"""
import base64
import json
import requests
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple
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

    def _find_sent_message_robust(
        self,
        headers: Dict,
        tracking_id: str,
        conversation_id: str,
        recipient_email: str,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Robustly find sent message using multiple strategies with retries.
        
        Strategy:
        1. Try to find by tracking header (most reliable)
        2. Fallback to conversation_id + recipient match
        3. Retry with increasing delays if not found
        
        Args:
            headers: Auth headers
            tracking_id: Unique tracking ID
            conversation_id: Conversation ID from draft
            recipient_email: Recipient email to verify
            max_retries: Number of retry attempts
            retry_delay: Initial delay between retries (seconds)
        
        Returns:
            Tuple of (message_id, conversation_id) or (None, None)
        """
        for attempt in range(max_retries):
            print(f"🔍 [DEBUG] Search attempt {attempt + 1}/{max_retries}")
            
            # Wait before searching (increases with each retry)
            wait_time = retry_delay * (attempt + 1)
            print(f"⏳ [DEBUG] Waiting {wait_time}s for message to appear in SentItems...")
            time.sleep(wait_time)
            
            # Query SentItems - get last 20 messages
            sent_url = "https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages"
            params = {
                "$top": 20,
                "$orderby": "sentDateTime desc",
                "$select": "id,conversationId,subject,toRecipients,sentDateTime,internetMessageHeaders"
            }
            
            try:
                response = requests.get(sent_url, headers=headers, params=params)
                response.raise_for_status()
                messages = response.json().get("value", [])
                
                print(f"📬 [DEBUG] Found {len(messages)} recent sent messages")
                
                # Strategy 1: Find by tracking header (most reliable)
                for msg in messages:
                    msg_headers = msg.get("internetMessageHeaders", [])
                    for header in msg_headers:
                        if header.get("name") == "X-Spine-Tracking-ID" and header.get("value") == tracking_id:
                            message_id = msg.get("id")
                            conv_id = msg.get("conversationId")
                            print(f"✅ [DEBUG] Found by tracking header!")
                            return (message_id, conv_id)
                
                print("⚠️ [DEBUG] Not found by tracking header, trying conversation_id...")
                
                # Strategy 2: Find by conversation_id + recipient
                for msg in messages:
                    if msg.get("conversationId") == conversation_id:
                        recipients = msg.get("toRecipients", [])
                        if recipients:
                            recipient = recipients[0]["emailAddress"]["address"]
                            if recipient.lower() == recipient_email.lower():
                                message_id = msg.get("id")
                                conv_id = msg.get("conversationId")
                                print(f"✅ [DEBUG] Found by conversation_id + recipient match!")
                                return (message_id, conv_id)
                
                print("⚠️ [DEBUG] Message not found in this attempt, will retry...")
                
            except Exception as e:
                print(f"❌ [DEBUG] Error during search: {str(e)}")
        
        # All retries exhausted
        print("❌ [DEBUG] Could not find sent message after all retries")
        return (None, None)

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
            print(f"📧 [DEBUG] reply_to_message_id: {reply_to_message_id}")
            print(f"📧 [DEBUG] conversation_id: {conversation_id}")

            # Get access token
            access_token = self._refresh_token_if_needed()
            print(f"🔑 [DEBUG] Got access token (length: {len(access_token)})")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # ============ FOLLOW-UP EMAIL (REPLY) ================
            if reply_to_message_id:
                print("🔄 [DEBUG] This is a FOLLOW-UP (reply)")
                print(f"🔗 [DEBUG] Original message ID: {reply_to_message_id}")
                print(f"🔗 [DEBUG] Conversation ID: {conversation_id}")

                # Generate unique tracking header
                tracking_id = str(uuid.uuid4())
                print(f"🔖 [DEBUG] Tracking ID: {tracking_id}")

                # Step 1: Get the original message to extract headers
                get_message_url = f"https://graph.microsoft.com/v1.0/me/messages/{reply_to_message_id}"
                params = {"$select": "subject,internetMessageId"}
                
                print(f"📤 [DEBUG] Fetching original message headers...")
                response = requests.get(get_message_url, headers=headers, params=params)
                if response.status_code == 401:
                    access_token = self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = requests.get(get_message_url, headers=headers, params=params)
                
                response.raise_for_status()
                original_message = response.json()
                original_subject = original_message.get("subject", "")
                internet_message_id = original_message.get("internetMessageId", "")
                
                print(f"✅ [DEBUG] Original subject: {original_subject}")
                print(f"✅ [DEBUG] Original internet message ID: {internet_message_id}")

                # Prepare subject with "Re:" if not already there
                follow_up_subject = original_subject
                if not follow_up_subject.lower().startswith("re:"):
                    follow_up_subject = f"Re: {original_subject}"

                # Step 2: Create a NEW message (not a reply) with threading headers
                create_message_url = "https://graph.microsoft.com/v1.0/me/messages"
                
                # Build extended properties for threading
                extended_props = []
                if internet_message_id:
                    # PidTagInReplyToId - links this message to the original
                    extended_props.append({
                        "id": "String 0x1042",
                        "value": internet_message_id
                    })
                
                message_payload = {
                    "subject": follow_up_subject,
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
                    ],
                    "internetMessageHeaders": [
                        {
                            "name": "X-Spine-Tracking-ID",
                            "value": tracking_id
                        }
                    ]
                }
                
                # Add extended properties if we have them
                if extended_props:
                    message_payload["singleValueExtendedProperties"] = extended_props

                print(f"📤 [DEBUG] Creating follow-up message draft...")
                response = requests.post(create_message_url, headers=headers, json=message_payload)
                if response.status_code == 401:
                    access_token = self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = requests.post(create_message_url, headers=headers, json=message_payload)

                response.raise_for_status()
                draft = response.json()
                draft_id = draft.get("id")
                draft_conversation_id = draft.get("conversationId")

                print(f"✅ [DEBUG] Follow-up draft created: {draft_id}")
                print(f"✅ [DEBUG] Draft conversation ID: {draft_conversation_id}")

                # Step 3: Send the draft
                send_url = f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}/send"
                print(f"📤 [DEBUG] Sending follow-up draft...")

                response = requests.post(send_url, headers=headers)
                response.raise_for_status()
                
                print("✅ [DEBUG] Follow-up sent successfully!")

                # Step 4: Retrieve the sent message with ROBUST SEARCH
                print("🔍 [DEBUG] Retrieving sent follow-up message...")
                
                sent_message_id, sent_conversation_id = self._find_sent_message_robust(
                    headers=headers,
                    tracking_id=tracking_id,
                    conversation_id=draft_conversation_id,
                    recipient_email=to_email,
                    max_retries=3,
                    retry_delay=2
                )
                
                if sent_message_id:
                    print(f"✅ [DEBUG] Successfully retrieved sent follow-up ID: {sent_message_id}")
                    return {
                        "message_id": sent_message_id,
                        "conversation_id": sent_conversation_id or conversation_id
                    }
                else:
                    print("⚠️ [DEBUG] Could not retrieve sent message, using draft IDs")
                    return {
                        "message_id": draft_id,
                        "conversation_id": conversation_id or draft_conversation_id
                    }

            # ============ INITIAL EMAIL ================
            else:
                print("📧 [DEBUG] This is an INITIAL email")

                # Generate unique tracking header
                tracking_id = str(uuid.uuid4())
                print(f"🔖 [DEBUG] Tracking ID: {tracking_id}")

                # Step 1: Create draft message with tracking header
                create_message_url = "https://graph.microsoft.com/v1.0/me/messages"
                message_payload = {
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
                    ],
                    "internetMessageHeaders": [
                        {
                            "name": "X-Spine-Tracking-ID",
                            "value": tracking_id
                        }
                    ]
                }

                print(f"📤 [DEBUG] Creating draft message...")
                response = requests.post(create_message_url, headers=headers, json=message_payload)
                if response.status_code == 401:
                    access_token = self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = requests.post(create_message_url, headers=headers, json=message_payload)

                response.raise_for_status()
                draft = response.json()
                draft_id = draft.get("id")
                draft_conversation_id = draft.get("conversationId")

                print(f"✅ [DEBUG] Draft created with ID: {draft_id}")
                print(f"✅ [DEBUG] Draft conversation ID: {draft_conversation_id}")

                # Step 2: Send the draft
                send_url = f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}/send"
                print(f"📤 [DEBUG] Sending draft message...")

                response = requests.post(send_url, headers=headers)
                response.raise_for_status()
                
                print("✅ [DEBUG] Draft sent successfully!")

                # Step 3: Retrieve the sent message with ROBUST SEARCH
                print("🔍 [DEBUG] Retrieving sent message with robust search...")
                
                sent_message_id, sent_conversation_id = self._find_sent_message_robust(
                    headers=headers,
                    tracking_id=tracking_id,
                    conversation_id=draft_conversation_id,
                    recipient_email=to_email,
                    max_retries=3,
                    retry_delay=2
                )
                
                if sent_message_id:
                    print(f"✅ [DEBUG] Successfully retrieved sent message ID: {sent_message_id}")
                    return {
                        "message_id": sent_message_id,
                        "conversation_id": sent_conversation_id
                    }
                else:
                    print("⚠️ [DEBUG] Could not retrieve sent message, using draft IDs as fallback")
                    return {
                        "message_id": draft_id,
                        "conversation_id": draft_conversation_id
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