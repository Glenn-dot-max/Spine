"""
Email service orchestrator for campaigns.
Coordinates template rendering, email sending, and database updates.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect
from app.services.email.template_renderer import email_renderer
from app.services.email.gmail_sender import send_email_via_gmail
from app.services.email.outlook_sender import send_email_via_outlook


class EmailService:
    """
    Manages campaign email sending workflow.
    """
    
    def __init__(self, db: Session):
        """
        Initialize email service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _get_template_name(self, sequence_step: int) -> str:
        """
        Get template filename based on email sequence step.
        
        Args:
            sequence_step: Current step (0, 1, 2, 3)
        
        Returns:
            Template filename
        """
        templates = {
            0: "initial.html",       # Premier email
            1: "followup_1.html",    # Relance 1
            2: "followup_2.html",    # Relance 2
            3: "followup_3.html",    # Relance 3
        }
        return templates.get(sequence_step, "initial.html")
    
    def _get_email_subject(self, campaign_name: str, sequence_step: int) -> str:
        """
        Generate email subject based on sequence step.
        
        Args:
            campaign_name: Name of the campaign
            sequence_step: Current step
        
        Returns:
            Email subject line
        """
        subjects = {
            0: f"Great meeting you at {campaign_name}",
            1: f"Following up - {campaign_name}",
            2: f"Last chance to connect - {campaign_name}",
            3: f"Thanks for your time at {campaign_name}",
        }
        return subjects.get(sequence_step, f"Following up from {campaign_name}")
    
    def send_campaign_email(
        self,
        campaign: Campaign,
        contact: CampaignContact,
        prospect: Prospect,
        user: User,
        template_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email to a campaign contact.
        
        This is the MAIN method - it does everything:
        1. Checks user has email configured
        2. Renders the template
        3. Sends via Gmail or Outlook
        4. Updates database with thread info
        
        Args:
            campaign: Campaign object
            contact: CampaignContact link
            prospect: Prospect to send to
            user: User sending the email
            template_override: Optional template name override
        
        Returns:
            Dictionary with send result:
                - success: bool
                - message_id: str
                - thread_id: str
                - provider: str (gmail or outlook)
        
        Raises:
            Exception: If user doesn't have email configured
            Exception: If sending fails
        """
        
        # STEP 1: Verify user has email configured
        if not user.has_email_configured:
            raise Exception("User does not have any email provider connected")
        
        # Determine which provider to use
        provider = user.default_email_provider
        
        if not provider:
            # Fallback: use whichever is connected
            if user.gmail_connected:
                provider = "gmail"
            elif user.outlook_connected:
                provider = "outlook"
            else:
                raise Exception("No email provider configured")
        
        # STEP 2: Get the right template
        if template_override:
            template_name = template_override
        else:
            template_name = self._get_template_name(contact.email_sequence_step)
        
        # STEP 3: Render the template with campaign + prospect data
        try:
            html_body = email_renderer.render_campaign_email(
                template_name=template_name,
                prospect_first_name=prospect.first_name,
                prospect_last_name=prospect.last_name,
                prospect_company=prospect.company_name or "your company",
                campaign_name=campaign.name,
                campaign_location=campaign.location,
                sender_name=f"{user.first_name} {user.last_name}" if user.first_name else "The Team",
                # Add any extra variables here
                distributor_name=campaign.distributor_name,
            )
        except Exception as e:
            raise Exception(f"Failed to render email template: {str(e)}")
        
        # STEP 4: Generate subject
        subject = self._get_email_subject(campaign.name, contact.email_sequence_step)
        
        # STEP 5: Send the email via the right provider
        try:
            if provider == "gmail":
                result = send_email_via_gmail(
                    user=user,
                    db=self.db,
                    to_email=prospect.email,
                    subject=subject,
                    html_body=html_body,
                    reply_to_message_id=contact.email_message_id,  # For threading
                    thread_id=contact.email_thread_id              # For threading
                )
            
            elif provider == "outlook":
                result = send_email_via_outlook(
                    user=user,
                    db=self.db,
                    to_email=prospect.email,
                    subject=subject,
                    html_body=html_body,
                    reply_to_message_id=contact.email_message_id,
                    conversation_id=contact.email_thread_id
                )
            
            else:
                raise Exception(f"Unknown email provider: {provider}")
            
        except Exception as e:
            # If token refresh fails or sending fails
            raise Exception(f"Failed to send email: {str(e)}")
        
        # STEP 6: Update database with send info
        contact.email_sequence_step += 1  # Increment step
        contact.last_email_sent_at = datetime.utcnow()  # Save timestamp
        
        # Save thread/message IDs for next email (threading)
        if result.get("message_id"):
            contact.email_message_id = result["message_id"]
        
        if result.get("thread_id"):
            contact.email_thread_id = result["thread_id"]
        elif result.get("conversation_id"):
            contact.email_thread_id = result["conversation_id"]
        
        # Update status to 'contacted' if this was first email
        if contact.email_sequence_step == 1 and contact.status == "pending":
            contact.status = "contacted"
        
        self.db.commit()
        
        # STEP 7: Return success result
        return {
            "success": True,
            "message_id": result.get("message_id", ""),
            "thread_id": result.get("thread_id") or result.get("conversation_id", ""),
            "provider": provider,
            "sequence_step": contact.email_sequence_step,
            "sent_to": prospect.email
        }
    
    def send_bulk_campaign_emails(
        self,
        campaign: Campaign,
        contacts: list[CampaignContact],
        user: User
    ) -> Dict[str, Any]:
        """
        Send emails to multiple campaign contacts.
        
        Args:
            campaign: Campaign object
            contacts: List of CampaignContact objects
            user: User sending the emails
        
        Returns:
            Dictionary with:
                - total: int (total contacts)
                - sent: int (successfully sent)
                - failed: int (failed to send)
                - errors: list of error details
        """
        total = len(contacts)
        sent = 0
        failed = 0
        errors = []
        
        for contact in contacts:
            # Get prospect data
            prospect = self.db.query(Prospect).filter(
                Prospect.id == contact.prospect_id
            ).first()
            
            if not prospect:
                failed += 1
                errors.append({
                    "prospect_id": contact.prospect_id,
                    "error": "Prospect not found"
                })
                continue
            
            try:
                # Send email to this contact
                result = self.send_campaign_email(
                    campaign=campaign,
                    contact=contact,
                    prospect=prospect,
                    user=user
                )
                sent += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    "prospect_id": prospect.id,
                    "prospect_email": prospect.email,
                    "error": str(e)
                })
        
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "errors": errors
        }