"""
Background scheduler — envoie les follow-ups dus toutes les 5 minutes.
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.campaign import Campaign, CampaignContact
from app.models.prospect import Prospect
from app.models.user import User
from app.services.email.email_service import EmailService
from apscheduler.schedulers.background import BackgroundScheduler


logger = logging.getLogger(__name__)


def get_effective_delay(contact: CampaignContact, campaign: Campaign, step: int):
    """
    Retourne le délai en jours pour le prochain follow-up.
    Priorité : délai custom du contact > délai par défaut de la campagne.
    Retourne None si séquence terminée (step > 3).
    """
    if step == 1:
        return contact.custom_followup_delay_1 or campaign.followup_delay_1
    elif step == 2:
        return contact.custom_followup_delay_2 or campaign.followup_delay_2
    elif step == 3:
        return contact.custom_followup_delay_3 or campaign.followup_delay_3
    else:
        return None


def schedule_next_followup(contact: CampaignContact, campaign: Campaign):
    """
    Calcule et assigne la prochaine date de follow-up après un envoi.
    Retourne la date planifiée ou None si séquence terminée.
    """
    delay = get_effective_delay(contact, campaign, contact.email_sequence_step)

    if delay is None:
        contact.next_follow_up_scheduled_at = None
        return None

    next_date = datetime.now(timezone.utc) + timedelta(days=delay)
    contact.next_follow_up_scheduled_at = next_date
    return next_date


def send_due_followups_task():
    """
    Background task : envoie tous les follow-ups dus.
    Runs every 5 minutes.
    """
    logger.info("🔄 [SCHEDULER] Starting send_due_followups_task...")
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # Trouve tous les contacts avec un follow-up dû
        contacts = db.query(CampaignContact).filter(
            CampaignContact.next_follow_up_scheduled_at.isnot(None),
            CampaignContact.next_follow_up_scheduled_at <= now,
            CampaignContact.status == "contacted"
        ).all()

        if not contacts:
            logger.info("✅ [SCHEDULER] No follow-ups due at this time.")
            return

        logger.info(f"📬 [SCHEDULER] Found {len(contacts)} follow-ups to send")

        sent_count = 0
        failed_count = 0
        email_service = EmailService(db)

        for contact in contacts:
            try:
                # Récupère la campagne
                campaign = db.query(Campaign).filter(Campaign.id == contact.campaign_id).first()
                if not campaign:
                    logger.error(f"❌ [SCHEDULER] Campaign {contact.campaign_id} not found")
                    failed_count += 1
                    continue

                # Récupère l'utilisateur
                user = db.query(User).filter(User.id == campaign.user_id).first()
                if not user:
                    logger.error(f"❌ [SCHEDULER] User {campaign.user_id} not found")
                    failed_count += 1
                    continue

                # Vérifie que l'email est configuré
                if not user.has_email_configured:
                    logger.warning(f"⚠️ [SCHEDULER] No email provider for user {user.id}")
                    failed_count += 1
                    continue

                # Récupère le prospect
                prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
                if not prospect:
                    logger.error(f"❌ [SCHEDULER] Prospect {contact.prospect_id} not found")
                    failed_count += 1
                    continue

                logger.info(f"✉️ [SCHEDULER] Sending follow-up to {prospect.email} (step {contact.email_sequence_step})")

                # Envoie l'email
                email_service.send_campaign_email(
                    campaign=campaign,
                    contact=contact,
                    prospect=prospect,
                    user=user,
                )

                # ✅ Planifie automatiquement le prochain follow-up
                next_date = schedule_next_followup(contact, campaign)

                db.commit()
                sent_count += 1

                if next_date:
                    logger.info(f"📅 [SCHEDULER] Next follow-up for {prospect.email} scheduled at {next_date}")
                else:
                    logger.info(f"✅ [SCHEDULER] Sequence complete for {prospect.email}")

            except Exception as e:
                logger.error(f"❌ [SCHEDULER] Failed for contact {contact.id}: {str(e)}")
                db.rollback()
                failed_count += 1

        logger.info(f"✅ [SCHEDULER] Done: {sent_count} sent, {failed_count} failed")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Fatal error: {str(e)}")
    finally:
        db.close()

# ================= SCHEDULER LIFECYCLE =================

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(send_due_followups_task, "interval", minutes=5)
    scheduler.start()
    logger.info("✅ [SCHEDULER] Started — running every 5 minutes")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("🛑 [SCHEDULER] Stopped")