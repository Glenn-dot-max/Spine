"""
SPINE V1 — email_composer
=========================
Rôle : Moteur de composition d'emails post-campagne par blocs conditionnels.
       Chaque bloc est généré automatiquement ou overridé par l'user.
       Retourne les blocs séparément pour permettre l'édition frontend bloc par bloc.

Architecture des blocs (dans l'ordre) :
  1. greeting          → contextuel selon campaign_source + nom prospect
  2. company_intro     → bloc présentation société (campaign.company_intro_text ou généré)
  3. catalog_pitch     → produits détectés OU présentation catalogue générale
  4. segment_note      → note spécifique si type_structure du prospect renseigné
  5. samples           → bloc samples seulement si campaign.offer_samples = True
  6. attachments       → mention PJ seulement si attachments passés
  7. cta               → 1 seul CTA clair, adapté au step de séquence
  8. signature         → sender

Séquence :
  step 0 = J0 (initial post-salon)
  step 1 = J+5 (follow-up 1)
  step 2 = J+14 (follow-up 2 — final)

Sources actives :
  trade_show  → ✅ Actif V1 Sprint 4
  ride_along  → 🔒 Coming soon
  outreach    → 🔒 Coming soon

Dépendances : app.models (Prospect, Company, Campaign, Product, User)
Utilisé par : routes/campaign_emails.py (preview + send)
Sécurité : pas de PII dans les logs; user_id filtré en amont.
À faire : ride_along + outreach sources; multi-langue EN/FR; AI improve par bloc.
Dernière modification : 2026-06-03 — refonte complète V1 blocs conditionnels.
"""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models.prospect import Prospect
from app.models.company import Company, ChainLevel, EndUserType
from app.models.campaign import Campaign, CampaignSource
from app.models.user import User


class EmailComposer:
    """
    Compose des emails post-campagne personnalisés par blocs conditionnels.

    Usage :
        result = EmailComposer.compose(
            prospect=prospect,
            campaign=campaign,
            sender=current_user,
            db=db,
            step=0,
            overrides={"company_intro": "Texte custom...", "cta": "..."}
        )

    Retourne un dict avec :
        - blocks  : chaque bloc de texte séparé (pour édition frontend)
        - subject : sujet de l'email
        - html_body : email HTML assemblé
        - text_body : email texte plain
        - preview_text : premier paragraphe pour aperçu
    """

    # ─────────────────────────────────────────────
    # BLOC 1 — GREETING
    # ─────────────────────────────────────────────

    @staticmethod
    def _greeting_block(
        campaign_source: CampaignSource,
        campaign_name: str,
        first_name: str,
        step: int,
    ) -> str:
        """Salutation contextuelle selon la source de campagne et le step."""
        if step == 0:
            if campaign_source == CampaignSource.trade_show:
                return (
                    f"Hi {first_name},\n\n"
                    f"It was great meeting you at {campaign_name}! "
                    "I wanted to follow up and share a bit more about what we do."
                )
            # Prêt pour plus tard
            elif campaign_source == CampaignSource.ride_along:
                return f"Hi {first_name},\n\nThank you for your time during our visit."
            else:
                return f"Hi {first_name},\n\nI wanted to reach out and introduce myself."

        elif step == 1:
            return (
                f"Hi {first_name},\n\n"
                "I wanted to follow up on my previous email — "
                "I hope you had a chance to review what I sent."
            )
        else:
            # step 2 — final
            return (
                f"Hi {first_name},\n\n"
                "I know things get busy — this is my last follow-up, "
                "I just didn't want to miss the opportunity to connect."
            )

    # ─────────────────────────────────────────────
    # BLOC 2 — COMPANY INTRO
    # ─────────────────────────────────────────────

    @staticmethod
    def _company_intro_block(
        company_intro_text: Optional[str],
    ) -> Optional[str]:
        """
        Présentation société/activité.
        Si l'user a renseigné company_intro_text → utiliser ça.
        Sinon → None (le bloc est omis).
        """
        if company_intro_text and company_intro_text.strip():
            return company_intro_text.strip()
        return None

    # ─────────────────────────────────────────────
    # BLOC 3 — CATALOG PITCH
    # ─────────────────────────────────────────────

    @staticmethod
    def _catalog_pitch_block(
        catalog_pitch_text: Optional[str],
        product_names: List[str],
        has_attachment: bool,
    ) -> str:
        """
        Présentation catalogue ou produits.
        Priorité :
          1. catalog_pitch_text (custom user) → utiliser tel quel
          2. product_names détectés → lister les produits
          3. Fallback générique → "please find our catalogue attached"
        """
        # 1. Custom user
        if catalog_pitch_text and catalog_pitch_text.strip():
            return catalog_pitch_text.strip()

        # 2. Produits détectés depuis l'import
        if product_names:
            product_list = ", ".join(product_names)
            return (
                f"Based on your interests, I wanted to highlight "
                f"our {product_list} — I think these could be a strong fit for your operation."
            )

        # 3. Fallback générique
        if has_attachment:
            return (
                "Please find attached our product catalogue — "
                "you'll find our full range of references along with pricing information."
            )
        return (
            "I'd love to share our product catalogue with you, "
            "which covers our full range of references. "
            "Just let me know and I'll send it right over."
        )

    # ─────────────────────────────────────────────
    # BLOC 4 — SEGMENT NOTE
    # ─────────────────────────────────────────────

    @staticmethod
    def _segment_note_block(
        campaign: Campaign,
        end_user_type: Optional[EndUserType],
    ) -> Optional[str]:
        """
        Note spécifique au segment du prospect.
        Injecte segment_note_global toujours si renseignée.
        Injecte segment_note_XXX selon end_user_type du prospect.
        """
        parts = []

        # Note spécifique au type d'end user
        foodservice_types = {
            EndUserType.restaurant, EndUserType.hotel,
            EndUserType.franchise, EndUserType.country_club,
            EndUserType.catering, EndUserType.institutional,
        }
        if end_user_type in foodservice_types and campaign.segment_note_restaurant:
            parts.append(campaign.segment_note_restaurant.strip())
        elif end_user_type == EndUserType.retail and campaign.segment_note_retail:
            parts.append(campaign.segment_note_retail.strip())

        # Note globale (toujours ajoutée si renseignée)
        if campaign.segment_note_global:
            parts.append(campaign.segment_note_global.strip())

        return "\n\n".join(parts) if parts else None

    # ─────────────────────────────────────────────
    # BLOC 5 — SAMPLES
    # ─────────────────────────────────────────────

    @staticmethod
    def _samples_block(
        offer_samples: bool,
        samples_note: Optional[str],
    ) -> Optional[str]:
        """
        Bloc samples — présent UNIQUEMENT si offer_samples = True.
        samples_note contient l'adresse ou les modalités.
        """
        if not offer_samples:
            return None

        if samples_note and samples_note.strip():
            return (
                f"I'd also love to send you some samples so you can see the quality firsthand — "
                f"{samples_note.strip()}"
            )
        return (
            "I'd be happy to send you some product samples so you can experience "
            "the quality directly. Just send me your shipping address and I'll get those out to you."
        )

    # ─────────────────────────────────────────────
    # BLOC 6 — ATTACHMENTS MENTION
    # ─────────────────────────────────────────────

    @staticmethod
    def _attachments_block(attachment_names: List[str]) -> Optional[str]:
        """
        Mention des pièces jointes — présent UNIQUEMENT si attachments passés.
        """
        if not attachment_names:
            return None
        names = ", ".join(attachment_names)
        return f"📎 Attached for your reference: {names}"

    # ─────────────────────────────────────────────
    # BLOC 7 — CTA
    # ─────────────────────────────────────────────

    @staticmethod
    def _cta_block(step: int, offer_samples: bool) -> str:
        """
        Un seul CTA clair par email.
        step 0 : invitation à un appel
        step 1 : relance + samples si activé
        step 2 : dernière chance
        """
        if step == 0:
            return (
                "Would you be open to a quick call next week? "
                "I'm happy to work around your schedule."
            )
        elif step == 1:
            if offer_samples:
                return (
                    "Would you like me to send over some samples along with our full catalogue? "
                    "Just reply with your shipping address."
                )
            return (
                "I'd love to set up a quick call to go over the details — "
                "when would work for you?"
            )
        else:
            # step 2 — final
            return (
                "If you're interested, I'm one reply away. "
                "If now isn't the right time, no worries — "
                "I'll make sure to follow up again next season."
            )

    # ─────────────────────────────────────────────
    # BLOC 8 — SIGNATURE
    # ─────────────────────────────────────────────

    @staticmethod
    def _signature_block(sender: User) -> str:
        """Signature de l'expéditeur."""
        name = f"{sender.first_name} {sender.last_name}".strip() or sender.email
        return f"Best regards,\n{name}\n{sender.email}"

    # ─────────────────────────────────────────────
    # SUJET EMAIL
    # ─────────────────────────────────────────────

    @staticmethod
    def _subject(
        campaign: Campaign,
        prospect_first_name: str,
        step: int,
    ) -> Optional[str]:
        """
        Sujet de l'email.

        step 0 = sujet initial, customisable par l'user.
        step 1+ = None → le threading email sender gère le Re: automatiquement
                  en utilisant email_thread_id + email_message_id du CampaignContact.

        L'user peut toujours override via overrides['subject'] pour n'importe quel step.
        """
        if step == 0:
            return f"Great meeting you at {campaign.name}, {prospect_first_name}"
        return None

    # ─────────────────────────────────────────────
    # ASSEMBLAGE HTML
    # ─────────────────────────────────────────────

    @staticmethod
    def _assemble_html(blocks: Dict[str, Optional[str]]) -> str:
        """Assemble les blocs en HTML propre."""
        paragraphs = []
        # Ordre fixe des blocs
        order = [
            "greeting",
            "company_intro",
            "catalog_pitch",
            "segment_note",
            "samples",
            "attachments",
            "cta",
            "signature",
        ]
        for key in order:
            text = blocks.get(key)
            if text:
                formatted = text.replace("\n", "<br>")
                paragraphs.append(f"<p>{formatted}</p>")

        body = "\n    ".join(paragraphs)
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    {body}
</body>
</html>"""

    @staticmethod
    def _assemble_text(blocks: Dict[str, Optional[str]]) -> str:
        """Assemble les blocs en texte plain."""
        order = [
            "greeting", "company_intro", "catalog_pitch",
            "segment_note", "samples", "attachments", "cta", "signature",
        ]
        parts = [blocks[k] for k in order if blocks.get(k)]
        return "\n\n".join(parts)

    # ─────────────────────────────────────────────
    # COMPOSE — POINT D'ENTRÉE PRINCIPAL
    # ─────────────────────────────────────────────

    @staticmethod
    def compose(
        prospect: Prospect,
        campaign: Campaign,
        sender: User,
        db: Session,
        step: int = 0,
        overrides: Optional[Dict[str, str]] = None,
        attachment_names: Optional[List[str]] = None,
    ) -> Dict:
        """
        Compose un email complet pour un prospect dans une campagne.

        Args:
            prospect         : Prospect ORM (avec company + product_interests chargés)
            campaign         : Campaign ORM
            sender           : User ORM (expéditeur)
            db               : Session SQLAlchemy
            step             : 0=J0, 1=J+5, 2=J+14
            overrides        : dict de blocs overridés par l'user {bloc_name: texte}
            attachment_names : liste des noms de PJ à mentionner dans l'email

        Returns:
            {
                "subject"      : str,
                "html_body"    : str,
                "text_body"    : str,
                "preview_text" : str,
                "blocks"       : dict (blocs éditables séparément)
            }

        Raises:
            NotImplementedError si campaign_source != trade_show
        """
        if overrides is None:
            overrides = {}
        if attachment_names is None:
            attachment_names = []

        # Vérif source active
        if campaign.campaign_source != CampaignSource.trade_show:
            raise NotImplementedError(
                f"Campaign source '{campaign.campaign_source}' is not yet supported. "
                "Only 'trade_show' is active in V1 Sprint 4."
            )

        # Résoudre company + end_user_type pour segmentation
        company: Optional[Company] = prospect.company
        end_user_type: Optional[EndUserType] = company.end_user_type if company else None

        # Résoudre produits d'intérêt
        product_names: List[str] = []
        if prospect.product_interests:
            from app.models.product import Product
            for pp in prospect.product_interests:
                if pp.product_id:
                    prod = db.query(Product).filter(Product.id == pp.product_id).first()
                    if prod:
                        product_names.append(prod.name)

        has_attachment = len(attachment_names) > 0

        # Générer chaque bloc (override utilisateur prioritaire)
        blocks: Dict[str, Optional[str]] = {
            "greeting": overrides.get("greeting") or EmailComposer._greeting_block(
                campaign.campaign_source, campaign.name, prospect.first_name, step
            ),
            "company_intro": overrides.get("company_intro") or EmailComposer._company_intro_block(
                campaign.company_intro_text
            ),
            "catalog_pitch": overrides.get("catalog_pitch") or EmailComposer._catalog_pitch_block(
                campaign.catalog_pitch_text, product_names, has_attachment
            ),
            "segment_note": overrides.get("segment_note") or EmailComposer._segment_note_block(
                campaign, end_user_type
            ),
            "samples": overrides.get("samples") or EmailComposer._samples_block(
                campaign.offer_samples, campaign.samples_note
            ),
            "attachments": overrides.get("attachments") or EmailComposer._attachments_block(
                attachment_names
            ),
            "cta": overrides.get("cta") or EmailComposer._cta_block(
                step, campaign.offer_samples
            ),
            "signature": overrides.get("signature") or EmailComposer._signature_block(sender),
        }

        subject = overrides.get("subject") or EmailComposer._subject(
            campaign, prospect.first_name, step
        )
        # subject = None pour step 1+ → signal à la route d'utiliser le thread existant (Re:)

        html_body = EmailComposer._assemble_html(blocks)
        text_body = EmailComposer._assemble_text(blocks)
        preview_text = (blocks.get("company_intro") or blocks.get("catalog_pitch") or "")[:100]

        return {
            "subject": subject,             # None pour follow-ups → threading géré par sender
            "html_body": html_body,
            "text_body": text_body,
            "preview_text": preview_text,
            "blocks": blocks,               # Blocs éditables séparément dans le frontend
            "attachment_names": attachment_names,  # Liste PJ passée telle quelle à la route d'envoi
        }


# Singleton importable
composer = EmailComposer()