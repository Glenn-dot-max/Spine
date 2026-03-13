"""
Email services for Spine CRM.
Handles template rendering and email sending via Gmail/Outlook.
"""
from .template_renderer import email_renderer, EmailTemplateRenderer
from .gmail_sender import send_email_via_gmail, GmailSender
from .outlook_sender import send_email_via_outlook, OutlookSender
from .email_service import EmailService

__all__ = [
    "email_renderer",
    "EmailTemplateRenderer",
    "send_email_via_gmail",
    "GmailSender",
    "send_email_via_outlook",
    "OutlookSender",
    "EmailService",
]