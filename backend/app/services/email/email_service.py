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
from app.models.email_template import EmailTemplate
from app.services.email.gmail_sender import send_email_via_gmail
from app.services.email.outlook_sender import send_email_via_outlook
from app.services.email.advanced_template_renderer import advanced_renderer


class EmailService:
    """
    Manages campaign email sending workflow.
    Now uses database templates with advanced rendering.
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
            0: "initial",    
            1: "followup_1", 
            2: "followup_2", 
            3: "followup_3", 
        }
        return templates.get(sequence_step, "initial")
    
    def _load_template(self, user: User, template_name: str, campaign: Optional[Campaign] = None) -> Optional[EmailTemplate]:
        
        # Priorité 1 : template spécifique à la campagne
        if campaign:
            template_id_map = {
                "initial": campaign.template_initial_id,
                "followup_1": campaign.template_followup_1_id,
                "followup_2": campaign.template_followup_2_id,
                "followup_3": campaign.template_followup_3_id,
            }
            template_id = template_id_map.get(template_name)
            if template_id:
                campaign_template = self.db.query(EmailTemplate).filter(
                    EmailTemplate.id == template_id,
                    EmailTemplate.is_active == True
                ).first()
                if campaign_template:
                    return campaign_template
                
        # Priorité 2 : template global de l'utilisateur
        user_template = self.db.query(EmailTemplate).filter(
            EmailTemplate.user_id == user.id,
            EmailTemplate.category == template_name,
            EmailTemplate.is_active == True
        ).first()
        if user_template:
            return user_template
        
        # Priorité 3 : template global
        return self.db.query(EmailTemplate).filter(
            EmailTemplate.user_id == None,
            EmailTemplate.category == template_name,
            EmailTemplate.is_active == True
        ).first()
    
    def _build_context(
            self,
            prospect: Prospect,
            campaign: Campaign,
            user: User,
    ) -> Dict[str, Any]:
        """
        Build context dictionary for template rendering.
        
        Args:
            prospect: Prospect object
            campaign: Campaign object
            user: User object

        Returns:
            Context dictionary with all variables for rendering
        """
        return {
            "prospect": {
                "first_name": prospect.first_name,
                "last_name": prospect.last_name,
                "email": prospect.email,
                "phone_number": prospect.phone_number,
                "position": prospect.position,
                "company_name": prospect.company_name,
                "company_size": prospect.company_size,
                "market": prospect.market,
            },
            "campaign": {
                "name": campaign.name,
                "location": campaign.location,
                "event_date": campaign.event_date.isoformat() if campaign.event_date else None,
                "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
                "distributor_name": campaign.distributor_name,
                "description": campaign.description,
            },
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }
        }
    
    def _get_fallback_subject(self, campaign_name: str, sequence_step: int) -> str:
        """
        Fallback subject of template not found.

        Args:
            campaign_name: Name of the campaign
            sequence_step: Email sequence step

        Returns:
            Subject line
        """
        subjects = {
            0: f"Great meeting you at {campaign_name}",
            1: f"Re: Great meeting you at {campaign_name}",
            2: f"Re: Great meeting you at {campaign_name}",
            3: f"Re: Great meeting you at {campaign_name}",
        }
        return subjects.get(sequence_step, f"Following up from {campaign_name}")

    def _get_fallback_body(
            self,
            prospect_first_name: str,
            campaign_name: str,
            campaign_location: str,
            user_first_name: str,
            user_last_name: str,
            sequence_step: int
    ) -> str:
        """
        Fallback email bidy f template not found.
        
        Returns:
            HTML email body
        """
        if sequence_step == 0:
            return f"""
<p>Hi {prospect_first_name},</p>
<p>It was great meeting you at <strong>{campaign_name}</strong> in {campaign_location}!</p>
<p>I wanted to follow up on our conversation.</p>
<p>Would you be available for a quick call this week?</p>
<p>Best regards,<br>
{user_first_name} {user_last_name}</p>
"""
        else:
            return f"""
<p>Hi {prospect_first_name},</p>
<p>Following up on my previous email about {campaign_name}.</p>
<p>Looking forward to hearing from you!</p>
<p>Best regards,<br>
{user_first_name} {user_last_name}</p>
"""
        
    def get_email_subject(self, campaign_name: str, sequence_step: int, original_subject: Optional[str] = None) -> str:
        """
        Generate elaik subject based on squence step.

        Args:
            campaign_name: Name of the campaign
            sequence_step: Current step
            original_subject: Original subject (for Re: threads)
        
        Returns:
            Email subject line
        """
        # For follow-ups use Re:
        if sequence_step > 0 and original_subject:
            return f"Re: {original_subject}"
        
        return self._get_fallback_subject(campaign_name, sequence_step)
    
    def send_campaign_email(
            self,
            campaign: Campaign,
            contact: CampaignContact,
            prospect: Prospect,
            user: User,
            template_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email to a campaign contact using database templates.

        This is the main method - it does everything:
        1. Loads template from database
        2. Renders tempates with context
        3. Sends via Gmail or Outlook
        4. Updates database with thread info

        Args: 
            campain: Campaign object
            contact: CampaignContact link
            prospect: Prospect to send to
            user: User sending the email
            template_override: Optional template name override

        Returns:
            Dictionary with send result

        Raises:
            Exception: If user doesn't have email configured
            Exception: If email sending fails
        """
        # Step 1: Verify user has email configured
        if not user.has_email_configured:
            raise Exception("User does not have any email provider connected")
        
        # Determine which provider to use
        provider = user.default_email_provider

        if not provider:
            if user.gmail_connected:
                provider = "gmail"
            elif user.outlook_connected:
                provider = "outlook"
            else:
                raise Exception("No email provider configured")
            
        # Step 2: Load template
        template_name = template_override or self._get_template_name(contact.email_sequence_step)
        template = self._load_template(user, template_name, campaign)

        # Step 3: Build context
        context = self._build_context(prospect, campaign, user)

        # Step 4: Render templates (with fallback)
        if template:
            try:
                subject = advanced_renderer.render(template.subject_template, context)
                html_body = advanced_renderer.render(template.body_template, context)

                if "<p>" not in html_body and "<br>" not in html_body:
                    html_body = html_body.replace("\n", "<br>")
            except Exception as e:
                raise Exception(f"Template rendering failed: {str(e)}")
            
        else:
            # Fallback to hardcoded templates
            subject = self._get_fallback_subject(campaign.name, contact.email_sequence_step)
            html_body = self._get_fallback_body(
                prospect.first_name,
                campaign.name,
                campaign.location or "our event",
                user.first_name or "Sales",
                user.last_name or "Team",
                contact.email_sequence_step
            )

        print(f"DEBUG SEND:")
        print(f"  sequence_step = {contact.email_sequence_step}")
        print(f"  reply_to_message_id = {contact.email_message_id}")
        print(f"  thread_id = {contact.email_thread_id}")


        # Step 5: Send email
        try:
            if provider == "gmail":
                result = send_email_via_gmail(
                    user = user,
                    db=self.db,
                    to_email=prospect.email,
                    subject=subject,
                    html_body=html_body,
                    reply_to_message_id=contact.email_message_id,
                    thread_id=contact.email_thread_id
                )

            elif provider == "outlook":
                result = send_email_via_outlook(
                    user = user,
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
            raise Exception(f"Failed to send email: {str(e)}")
        
        # Step 6: Update database with send info
        contact.email_sequence_step += 1
        contact.last_email_sent_at = datetime.utcnow()

        # Save thread/message IDs for threading
        if result.get("message_id"):
            contact.email_message_id = result["message_id"]
        
        if result.get("thread_id"):
            contact.email_thread_id = result["thread_id"]
        elif result.get("conversation_id"):
            contact.email_thread_id = result["conversation_id"]

        # Update status to 'contacted' if first email
        if contact.email_sequence_step == 1 and contact.status == "pending":
            contact.status = "contacted"
        
        if campaign.status.value == "upcoming":
            from app.models.campaign import TradeShowStatus
            campaign.status = TradeShowStatus.ACTIVE
        
        from app.routes.followups import schedule_next_followup
        schedule_next_followup(contact, campaign)

        from app.models.campaign import TradeShowStatus
        all_contacts = self.db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign.id
        ).all()
        if all(c.email_sequence_step >= 4 for c in all_contacts):
            campaign.status = TradeShowStatus.COMPLETED

        self.db.commit()

        # Step 7: Return success result
        return {
            "success": True,
            "message_id": result.get("message_id", ""),
            "thread_id": result.get("thread_id") or result.get("conversation_id", ""),
            "provider": provider,
            "sequence_step": contact.email_sequence_step,
            "sent_to": prospect.email,
            "template_used": template_name if template else "fallback"
        }
    
    def send_bulk_campaign_emails(
            self, 
            campaign: Campaign,
            contacts: list[CampaignContact],
            user: User,
    ) -> Dict[str, Any]:
        """
        Send emails to multiple campaign contacts.
        
        Args: 
            campaign: Campaign object
            contacts: List of CampaignContact objects
            user: User sending the emails
            
        Returns:
            Dictionary with summary of send results
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
                result = self.send_campaign_email(
                    campaign=campaign,
                    contact=contact,
                    prospect=prospect,
                    user=user
                )
                sent += 1

            except Exception as e:
                import traceback
                traceback.print_exc()
                failed += 1
                errors.append({
                    "prospect_id": contact.prospect_id,
                    "prospect_email": prospect.email,
                    "error": str(e)
                })

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "errors": errors
        }