"""
SPINE V1 - followup_utils
==========================
Rôle : Calcul et planification des dates de follow-up.
       Extrait de routes/followups.py pour éviter un import circulaire
       (email_service.py est un service qui ne doit pas importer depuis les routes).
Dépendances : app.models.campaign
Utilisé par : app.services.email.email_service, app.routes.followups
Sécurité : -
À faire : -
Dernière modification : 2026-05-25 — extraction de la logique de calcul des follow-ups dans un utilitaire dédié pour éviter les imports circulaires
"""

from datetime import datetime, timedelta
from typing import Optional

from app.models.campaign import Campaign, CampaignContact

def get_effective_delay(contact: CampaignContact, campaign: Campaign, step: int) -> Optional[int]:
  """
  Retourne le délai effectif en jours pour le prochain follow-up.
  Priorité : délai custom du contact > délai par défaut de la campagne.
  step : email_sequence_step APRÈS envoi (1, 2, 3)
  Retourne None si plus de follow-up à planifier (step > 3).
  """
  if step == 1:
    return contact.custom_followup_delay_1 or campaign.followup_delay_1
  elif step == 2:
    return contact.custom_followup_delay_2 or campaign.followup_delay_2
  elif step == 3:
    return contact.custom_followup_delay_3 or campaign.followup_delay_3
  else:
    return None
  
def schedule_next_followup(contact: CampaignContact, campaign: Campaign) -> Optional[datetime]:
  """
  Calcule et assigne la prochaine date de follow-up après un envoi.
  Retourne la date planifiée ou None si séquence terminée.
  """
  delay = get_effective_delay(contact, campaign, contact.email_sequence_step)

  if delay is None:
    contact.next_follow_up_scheduled_at = None
    return None
  
  next_date = datetime.utcnow() + timedelta(days=delay)
  contact.next_follow_up_scheduled_at = next_date
  return next_date