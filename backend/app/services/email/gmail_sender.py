"""
Gmail email sender using OAuth tokens.
Sends emails via Gmail API and handles token refresh.
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.oauth.gmail_oauth import refresh_gmail_token
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


class GmailSender:
    """
    Sends emails via Gmail API using user's OAuth tokens.
    """
    
    def __init__(self, user: User, db: Session):
        """
        Initialize Gmail sender for a specific user.
        
        Args:
            user: User object with Gmail OAuth tokens
            db: Database session (to save refreshed tokens)
        """
        self.user = user
        self.db = db
        
        # Verify user has Gmail connected
        if not user.gmail_connected:
            raise ValueError("User does not have Gmail connected")
        
        if not user.gmail_access_token:
            raise ValueError("User does not have Gmail access token")
    
    def _get_credentials(self) -> Credentials:
        """
        Get Gmail credentials and refresh if needed.
        
        Returns:
            Valid Gmail OAuth credentials
        """
        # Create credentials object
        credentials = Credentials(
            token=self.user.gmail_access_token,
            refresh_token=self.user.gmail_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=[
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly'
            ]
        )
        
        # Check if token is expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            # Save new access token to database
            self.user.gmail_access_token = credentials.token
            self.db.commit()
        
        return credentials
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        reply_to_message_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Send an email via Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            reply_to_message_id: Message ID to reply to (for threading)
            thread_id: Gmail thread ID (for threading)
        
        Returns:
            Dictionary with:
                - message_id: Gmail message ID
                - thread_id: Gmail thread ID
        
        Raises:
            Exception: If sending fails
        """
        try:
            # Get valid credentials
            credentials = self._get_credentials()
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create email message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['From'] = self.user.gmail_email
            message['Subject'] = subject
            
            # Add reply-to headers for threading
            if reply_to_message_id:
                message['In-Reply-To'] = reply_to_message_id
                message['References'] = reply_to_message_id
            
            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Encode message for Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Prepare send request
            send_request = {
                'raw': raw_message
            }
            
            # Add thread ID if replying
            if thread_id:
                send_request['threadId'] = thread_id
            
            # Send the email
            sent_message = service.users().messages().send(
                userId='me',
                body=send_request
            ).execute()
            
            # Return message ID and thread ID for database storage
            # Get the sent message to retrieve RFC 2822 Message-ID
            sent_msg_full = service.users().messages().get(
                userId='me',
                id=sent_message['id'],
                format='metadata',
                metadataHeaders=['Message-ID']
            ).execute()

            # Extract RFC 2822 Message-ID from headers
            rfc_message_id = None
            for header in sent_msg_full.get('payload', {}).get('headers', []):
                if header['name'].lower() == 'message-id':
                    rfc_message_id = header['value']
                    break

            # Return both Gmail ID (for API) and RFC Message-ID (for threading)
            return {
                "message_id": rfc_message_id or sent_message['id'],  # Prefer RFC ID
                "thread_id": sent_message['threadId']
            }
            
        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")
        except Exception as e:
            raise Exception(f"Failed to send email via Gmail: {str(e)}")


def send_email_via_gmail(
    user: User,
    db: Session,
    to_email: str,
    subject: str,
    html_body: str,
    reply_to_message_id: Optional[str] = None,
    thread_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Convenience function to send email via Gmail.
    
    Args:
        user: User with Gmail OAuth connected
        db: Database session
        to_email: Recipient
        subject: Subject line
        html_body: HTML email content
        reply_to_message_id: For threading (optional)
        thread_id: For threading (optional)
    
    Returns:
        Dict with message_id and thread_id
    """
    sender = GmailSender(user, db)
    return sender.send_email(to_email, subject, html_body, reply_to_message_id, thread_id)