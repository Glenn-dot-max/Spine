"""
SPINE V1 — email_composer
=========================
Rôle : Moteur de composition d'emails dynamiques par blocs.
       Assemble salutation, intro, produits, CTA selon contexte prospect + campagne.
Dépendances : app.models (Prospect, Company, ProspectProduct, Campaign, Product)
Utilisé par : routes/campaign_emails.py (preview + send)
Sécurité : user_id filtré via prospect.user_id; pas de PII en logs.
À faire : templates multi-langue (EN/FR); raffinement CTA par segment.
Dernière modification : 2026-06-03 — architecture initiale blocs dynamiques.
"""
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from app.models.prospect import Prospect, ProspectCanal
from app.models.company import StructureType
from app.models.campaign import Campaign
from app.models.user import User


class EmailComposer:
    """Compose des emails personnalisés par blocs dynamiques."""

    # ─────────────────────────────────────────────
    # BLOCS — SALUTATION
    # ─────────────────────────────────────────────

    @staticmethod
    def greeting_block(canal: Optional[ProspectCanal], prospect_first_name: str) -> str:
        """Retourne la salutation contextuelle selon le canal marketing."""
        greeting = f"Hi {prospect_first_name},"

        if canal == ProspectCanal.trade_show:
            return f"{greeting}\n\nIt was great meeting you at the show!"
        elif canal == ProspectCanal.linkedin:
            return f"{greeting}\n\nI came across your profile and thought we should connect."
        elif canal == ProspectCanal.referral:
            return f"{greeting}\n\nA colleague highly recommended we connect."
        elif canal == ProspectCanal.emailing:
            return f"{greeting}\n\nI wanted to reach out about an opportunity."
        elif canal == ProspectCanal.inbound:
            return f"{greeting}\n\nThanks for reaching out!"
        else:
            return greeting

    # ─────────────────────────────────────────────
    # BLOCS — INTRO MÉTIER
    # ─────────────────────────────────────────────

    @staticmethod
    def structure_intro_block(
        structure_type: Optional[StructureType],
        company_name: str,
    ) -> str:
        """Intro contextuelle selon le type de structure client."""
        if structure_type == StructureType.industry:
            return (
                f"For your industrial operation at {company_name}, "
                "we specialize in bulk formats, private label solutions, "
                "and operational efficiency at scale."
            )
        elif structure_type == StructureType.foodservice:
            return (
                f"For your multi-unit foodservice operation, {company_name} can benefit from our "
                "product range designed for high-volume, consistent quality, "
                "and cost optimization across locations."
            )
        elif structure_type == StructureType.retail:
            return (
                f"For your retail operation, we offer premium product positioning, "
                f"attractive margins, and proven shelf performance to drive "
                f"category growth at {company_name}."
            )
        else:
            return f"We work with operations like {company_name} to drive growth and efficiency."

    # ─────────────────────────────────────────────
    # BLOCS — PRODUITS
    # ─────────────────────────────────────────────

    @staticmethod
    def product_pitch_block(
        product_names: List[str],
        structure_type: Optional[StructureType],
    ) -> str:
        """Pitch produit personnalisé selon intérêts du prospect et sa structure."""
        if not product_names:
            return (
                "Whether you're looking to expand your product line or optimize existing SKUs, "
                "we have solutions tailored to your operation."
            )

        product_list = ", ".join(product_names)

        if structure_type == StructureType.industry:
            return (
                f"Our {product_list} line offers exceptional quality, "
                "compliance, and scalability for industrial-scale operations. "
                "We support private labeling and custom formats."
            )
        elif structure_type == StructureType.foodservice:
            return (
                f"Our {product_list} line is designed for high-volume foodservice: "
                "consistent quality, convenient formats, and competitive pricing. "
                "Available in bulk and case quantities."
            )
        elif structure_type == StructureType.retail:
            return (
                f"Our {product_list} line offers premium positioning for your shelves, "
                "strong margin potential, and proven consumer appeal. "
                "We handle marketing support and promotional opportunities."
            )
        else:
            return f"Our {product_list} line could be a strong fit for your operation."

    # ─────────────────────────────────────────────
    # BLOCS — APPEL À L'ACTION
    # ─────────────────────────────────────────────

    @staticmethod
    def call_to_action_block(
        canal: Optional[ProspectCanal],
        email_sequence_step: int,
        company_name: str,
    ) -> str:
        """CTA contextuelle selon le canal et le step de séquence."""
        # J0 — initial
        if email_sequence_step == 0:
            if canal == ProspectCanal.trade_show:
                return (
                    f"Would you be open to a quick call next week to discuss how we can support {company_name}? "
                    "I'm happy to work around your schedule."
                )
            elif canal == ProspectCanal.linkedin:
                return (
                    "I'd love to schedule a brief call to learn more about your needs and "
                    "share how we can help. Are you available this week?"
                )
            else:
                return (
                    "Would a quick call work for you next week to explore this opportunity? "
                    "Let me know what works best."
                )

        # J+5 — relance 1
        elif email_sequence_step == 1:
            return (
                "I'm including a detailed product sheet and would love to send a sample your way. "
                "When would be a good time to follow up?"
            )

        # J+14 — relance 2 (dernière chance)
        elif email_sequence_step == 2:
            return (
                "This is my final note — I'd hate to miss the opportunity to work with you. "
                "Are you still interested in learning more? "
                "Reply directly or call me if you'd like to discuss."
            )

        else:
            return "Looking forward to connecting!"

    # ─────────────────────────────────────────────
    # BLOCS — SIGNATURE
    # ─────────────────────────────────────────────

    @staticmethod
    def signature_block(sender: User) -> str:
        """Signature email du sender."""
        return f"Best regards,\n{sender.first_name} {sender.last_name}\n{sender.email}"

    # ─────────────────────────────────────────────
    # COMPOSITION — MAIN
    # ─────────────────────────────────────────────

    @staticmethod
    def compose(
        prospect: Prospect,
        campaign: Campaign,
        sender: User,
        db: Session,
        email_sequence_step: int = 0,
    ) -> Dict[str, str]:
        """
        Compose un email complet pour un prospect dans une campagne.

        Args:
            prospect           : Prospect ORM object (avec product_interests chargés)
            campaign           : Campaign ORM object
            sender             : User ORM object (expéditeur)
            db                 : Session SQLAlchemy
            email_sequence_step: 0=initial, 1=follow-up 1, 2=follow-up 2

        Returns:
            dict avec subject, html_body, text_body, preview_text
        """
        # Résoudre company
        company = prospect.company
        if company:
            company_name = company.name
            structure_type = company.type_structure
        else:
            company_name = prospect.company_name or "your operation"
            structure_type = None

        # Résoudre les produits d'intérêt
        product_names: List[str] = []
        if prospect.product_interests:
            from app.models.product import Product
            for pp in prospect.product_interests:
                if pp.product_id:
                    prod = db.query(Product).filter(Product.id == pp.product_id).first()
                    if prod:
                        product_names.append(prod.name)

        # Assembler les blocs
        greeting = EmailComposer.greeting_block(prospect.canal, prospect.first_name)
        intro    = EmailComposer.structure_intro_block(structure_type, company_name)
        pitch    = EmailComposer.product_pitch_block(product_names, structure_type)
        cta      = EmailComposer.call_to_action_block(prospect.canal, email_sequence_step, company_name)
        sig      = EmailComposer.signature_block(sender)

        # HTML body
        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>{greeting.replace(chr(10), '<br>')}</p>
    <p>{intro}</p>
    <p>{pitch}</p>
    <p>{cta}</p>
    <p>{sig.replace(chr(10), '<br>')}</p>
</body>
</html>"""

        # Text body (fallback sans HTML)
        text_body = f"{greeting}\n\n{intro}\n\n{pitch}\n\n{cta}\n\n{sig}"

        # Subject selon step
        step_subjects = {
            0: f"Connecting from {campaign.name} — {prospect.first_name}",
            1: f"Quick follow-up from {campaign.name}",
            2: f"Final note from {campaign.name}",
        }
        subject = step_subjects.get(email_sequence_step, f"Follow-up from {campaign.name}")

        return {
            "subject": subject,
            "html_body": html_body.strip(),
            "text_body": text_body.strip(),
            "preview_text": intro[:80] + "...",
        }


# Singleton importable
composer = EmailComposer()