"""
Background scheduler for automated tasks.
Handles follow-up sending and response checking.
"""
import logging
from datetime import datetime, timezone
from appscheduler.schedulers.background import BackgroundScheduler
from appscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.campaign_contact import CampaignContact, FollowUpStatus
from app.models.campaign import Campaign
from app.models.prospect import Prospect
from app.models.user import User
from app.sevices.email.email_service import EmailService
from app.services.email.gmail_response_checker import check_gmail_responses
from app.services.email.outlook_response_checker import check_outlook_responses

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global scheduler instance
scheduler = None

def send_due_followups_task():
    """
    Background task: Send all follow-ups that are due. 
    Runs every 5 minutes.
    """
    logger.info("🔄 [SCHEDULER] Starting send_due_followups_tasks...")
    db: Session = SessionLocal()

    try:
        # Find all contacts with follow-ups due
        now = datetime.now(timezone.utc)

        contacts = db.query(CampaignContact).filter(
            CampaignContact.follow_up_scheduled_at <= now,
            CampaignContact.follow_up_status == FollowUpStatus.PENDING
        ).all()

        if not contacts:
            logger.info("✅ [SCHEDULER] No follow-ups due at this time.")
            return

        logger.info(f"📬 [SCHEDULER] Found {len(contacts)} follow-ups to send")

        sent_count = 0
        failed_count = 0

        for contact in contacts:
            try:
                # Get user (for owner)
                campaign = db.query(Campaign).filter(Campaign.id == contact.campaign_id).first()
                if not campaign:
                    logger.error(f"❌ [SCHEDULER] Campaign {contact.campaign_id} not found")
                    continue

                user = db.query(User).filter(User.id == campaign.owner_id).first()
                if not user:
                    logger.error(f"❌ [SCHEDULER] User {campaign.owner_id} not found")
                    continue

                # Check email provider connected
                if not user.has_email_configured:
                    logger.warning(f"⚠️ [SCHEDULER] No email provider connected for user {user.id}")
                    contact.follow_up_status = FollowUpStatus.FAILED
                    db.commit()
                    failed_count += 1
                    continue

                # Get prospect
                prospect = db.query(Prospect).filter(Prospect.id == contact.prospect_id).first()
                if not prospect:
                    logger.error(f"❌ [SCHEDULER] Prospect {contact.prospect_id} not found")
                    continue

                logger.info(f"✉️ [SCHEDULER] Sending follow-up to {prospect.email} for campaign {campaign.name}")

                # use EmailService - it handles template, threading...
                result = email_service.send_campaign_email(
                    campaign=campaign,
                    contact=contact,
                    prospect=prospect,
                    user=user,
                )

                # Update follow-up status
                contact.follow_up_status = FollowupStatus.SENT
                contact.follow_up_sent_at = datetime.now(timezone.utc)

                db.commit()
                sent_count += 1
                logger.info(f"✅ [SCHEDULER] Follow-up sent to {prospect.email}")

            except Exception as e:
                logger.error(f"❌ [SCHEDULER] Failed to send follow-up to contact {contact.id}: {str(e)}")
                contact.follow_up_status = FollowUpStatus.FAILED
                db.commit()
                failed_count += 1

            logger.info(f"✅ [SCHEDULER] Follow-ups complete: {sent_count} sent, {failed_count} failed")

            except Exception as e:
                logger.error(f"❌ [SCHEDULER] Error in send_due_followups_task: {str(e)}")
            finally:
                db.close()


def check_responses_task():
    """
    Background task: Check for new email responses.
    Runs every 15 minutes.
    """
    logger.info("🔄 [SCHEDULER] Starting check_responses_task...")
    db = SessionLocal()

    try:
        # Get all users with email connected
        users = db.query(User).filter(
            (User.gmail_connected == True) | (User.outlook_connected == True)
        ).all()

        if not users:
            logger.info("✅ [SCHEDULER] No users with email connected.")
            return

        logger.info(f"📬 [SCHEDULER] Checking responses for {len(users)} users")

        total_responses = 0

        for user in users:
            try:
                if user.gmail_connected:
                    logger.info(f"📧 [SCHEDULER] Checking Gmail responses for user {user.id}")
                    result = check_gmail_responses(user, db)
                    total_responses += result.get("new_responses_count", 0)

                if user.outlook_connected:
                    logger.info(f"📧 [SCHEDULER] Checking Outlook responses for user {user.id}")
                    result = check_outlook_responses(user, db)
                    total_responses += result.get("new_responses_count", 0)

            except Exception as e:
                logger.error(f"❌ [SCHEDULER] Error checking responses for user {user.id}: {str(e)}")

        logger.info(f"✅ [SCHEDULER] Response checking complete: {total_responses} new responses found")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Error in check_responses_task: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    """
    Start the background scheduler and add tasks.
    """
    global scheduler
    if scheduler is not None:
        logger.warning("⚠️ [SCHEDULER] Scheduler already running")
        return

    logger.info("🚀 [SCHEDULER] Starting background scheduler...")

    scheduler = BackgroundScheduler(timezone="UTC")

    # TAsk 1: Send due follow-ups every 5 minutes
    scheduler.add_job(
        func=send_due_followups_task,
        trigger=IntervalTrigger(minutes=5),
        id="send_followups",
        name="Send due follow-upd",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60
    )

    # Task 2: Check for responses every 15 minutes
    scheduler.add_job(
        func=check_responses_task,
        trigger=IntervalTrigger(minutes=15),
        id="check_responses",
        name="Check email responses",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=120
    )

    scheduler.start()
    logger.info("✅ [SCHEDULER] Background scheduler started successfully")
    logger.info("📋 [SCHEDULER] Active jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id}, Next run: {job.next_run_time})")

def stop_scheduler():
    """
    Stop the background scheduler.
    """
    global scheduler
    if scheduler is None:
        logger.warning("⚠️ [SCHEDULER] Scheduler is not running")
        return

    logger.info("🛑 [SCHEDULER] Stopping background scheduler...")
    scheduler.shutdown(wait=False)
    scheduler = None
    logger.info("✅ [SCHEDULER] Background scheduler stopped successfully")

def get_scheduler_status():
    """
    Get the current status of the background scheduler.
    """
    global scheduler

    if scheduler is None or not scheduler.running:
        return {
            "running": False,
            "jobs": []
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "running": True,
        "jobs": jobs
    }