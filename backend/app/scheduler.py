"""
SPINE V1 - scheduler
==========================
Rôle : Jobs APScheduler lancés en arrière-plan au démarrage de l'app.
       Job 1 : envoie les follow-ups dus toutes les 5 minutes.
       Job 2 : vérifie les réponses email toutes les 2 heures.
               Si réponse détectée -> status "responded", stop séquence.
Dépendances : app.services.email.email_service,
              app.services.email.gmail_response_checker,
              app.services.email.outlook_response_checker,
              app.services.followup_utils
Utilisé par : app.main (start_scheduler / stop_scheduler)
Sécurité : chaque requête DB filtrée par user_id via campaign.user_id
À faire : notifications email deep link (Sprint 2 Task 5)
Dernière modification : 2026-05-28 - ajout jobdétection réponses toutes les 2h.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect
from app.models.user import User
from app.services.email.email_service import EmailService
from app.services.followup_utils import schedule_next_followup
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# ================ JOB 1 : FOLLOW-UPS ===================
def send_due_followups_tasks():
    """
    Background task : envoie les follow-ups dues.
    Tourne toutes les 5 minutes.
    Ne traite pas les contacts avec status="contacted" (pas oven/fridge/trash/converted).
    """
    logger.info("🔄 [SCHEDULER] Starting send_due_followups_tasks...")
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        contacts = db.query(CampaignContact).filter(
            CampaignContact.next_follow_up_scheduled_at.isnot(None),
            CampaignContact.next_follow_up_scheduled_at <= now,
            CampaignContact.status == "contacted"
        ).all()

        if not contacts:
            logger.info("✅ [SCHEDULER] No follow-ups due at this time.")
            return
        
        logger.info(f"📬 [SCHEDULER] Found {len(contacts)} follow-ups send")

        sent_count = 0
        failed_count = 0
        email_service = EmailService(db)

        for contact in contacts:
            try:
                campaign = db.query(Campaign).filter(Campaign.id == contact.campaign_id).first()
                if not campaign:
                    logger.error(f"❌ [SCHEDULER] Campaign {contact.campaign_id} not found")
                    failed_count += 1
                    continue

                user = db.query(User).filter(User.id == campaign.user_id).first()
                if not user:
                    logger.error(f"❌ [SCHEDULER] User {campaign.user_id} not found")
                    failed_count += 1
                    continue

                if not user.has_email_configured:
                    logger.warning(f"⚠️ [SCHEDULER] No email provider for user {user.id}")
                    failed_count += 1
                    continue

                prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
                if not prospect:
                    logger.error(f"❌ [SCHEDULER] Prospect {contact.prospect_id} not found")
                    failed_count += 1
                    continue

                logger.info(f"✉️ [SCHEDULER] Sending follow-up email to {prospect.email} (step {contact.email_sequence_step})")

                email_service.send_campaign_email(
                    campaign=campaign,
                    contact=contact,
                    prospect=prospect,
                    user=user,
                )

                next_date = schedule_next_followup(contact, campaign)
                db.commit()
                sent_count += 1

                if next_date:
                    logger.info(f"⏭️ [SCHEDULER] Next follow-up for {prospect.email} scheduled at {next_date}")
                else:
                    logger.info(f"✅ [SCHEDULER] No more follow-ups for {prospect.email}, sequence completed.")

            except Exception as e:
                logger.error(f"❌ [SCHEDULER] Failed for contact {contact.id}: {str(e)}")
                db.rollback()
                failed_count += 1

        logger.info(f"📊 [SCHEDULER] Done: {sent_count} sent, {failed_count} failed")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Fatal error in followups: {str(e)}")
    finally:
        db.close()


# ================ JOB 2 : DÉTECTION RÉPONSES ===================
def check_email_responses_task():
    """
    Background task : vérifie les réponses email pour tous les contacts "contacted".
    Tourne toutes les 2 heures.
    Si réponses détectée:
        - contact.status -> "responded"
        - contact.next_follow_up_scheduled_at -> None (stop séquence auto)
        - contact.respinse_received_at -> datetime UTC
    """
    logger.info("🔍 [SCHEDULER] Starting check_email_responses_task...")
    db: Session = SessionLocal()

    try:
        from app.services.email.gmail_response_checker import check_gmail_thread_for_response
        from app.services.email.outlook_response_checker import check_outlook_conversation_for_response

        # Récupère tous les contacts qui attendent encore une réponse
        contacts = db.query(CampaignContact).filter(
            CampaignContact.status == "contacted",
            CampaignContact.email_thread_id.isnot(None),
        ).all()

        if not contacts:
            logger.info("✅ [SCHEDULER] No contacts awaiting response at this time.")
            return
        
        logger.info(f"🔍 [SCHEDULER] Checking {len(contacts)} contacts for responses...")

        found_count = 0
        error_count = 0

        for contact in contacts:
            try:
                campaign = db.query(Campaign).filter(Campaign.id == contact.campaign_id).first()
                if not campaign:
                    continue

                user = db.query(User).filter(User.id == campaign.user_id).first()
                if not user or not user.has_email_configured:
                    continue

                prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
                if not prospect:
                    continue

                # Choisit le bon provider
                provider = user.default_email_provider
                if not provider:
                    provider = "gmail" if user.gmail_connected else "outlook"
                
                if provider == "gmail" and user.gmail_connected:
                    response_data = check_gmail_thread_for_response(
                        user=user,
                        db=db,
                        thread_id=contact.email_thread_id,
                        prospect_email=prospect.email
                    )
                elif provider == "outlook" and user.outlook_connected:
                    response_data = check_outlook_conversation_for_response(
                        user=user,
                        db=db,
                        conversation_id=contact.email_thread_id,
                        prospect_email=prospect.email
                    )
                else:
                    continue

                if response_data.get("has_response"):
                    contact.status = "responded"
                    contact.response_received_at = datetime.now(timezone.utc)
                    contact.last_response_content = response_data.get("response_content")
                    contact.next_follow_up_scheduled_at = None  # Stop séquence auto
                    db.commit()
                    found_count += 1
                    logger.info(f"📩 [SCHEDULER] Response detected from {prospect.email} - sequence stopped")

            except Exception as e:
                logger.error(f"❌ [SCHEDULER] Error checking responses for contact {contact.id}: {str(e)}")
                db.rollback()
                error_count += 1

        logger.info(f"📊 [SCHEDULER] Done checking responses: {found_count} found, {error_count} errors")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Fatal error in response checking: {str(e)}")
    finally:
        db.close()


# ================ SCHEDULER LIFECYCLE ===================

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(send_due_followups_tasks, "interval", minutes=5, id="followups")
    scheduler.add_job(check_email_responses_task, "interval", hours=2, id="response_check")
    scheduler.start()
    logger.info("🚀 [SCHEDULER] Scheduler started with follow-ups every 5 minutes and response checks every 2 hours")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("🛑 [SCHEDULER] Scheduler stopped")