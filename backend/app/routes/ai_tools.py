"""
SPINE V1 - ai_tools
==========================
Role: On-demand AI endpoints for the frontend (Starter plan).
      Improve email body: rewrites a drafted email for clarity and tone.
Dependencies: anthropic, app.core.confign app.core.deps
Used by: frontend WizardTemplatesStep (Improve button)
Security: Only the email bidy text is sent to Haiku - no PII (no email address, no last name). User must be authenticated.
Last modified: 2026-06-22 - creation, improve-email endpoint
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import anthropic

from app.core.config import ANTHROPIC_API_KEY
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/ai", tags=["ai"])

class ImproveEmailRequest(BaseModel):
    body: str

class ImproveEmailResponse(BaseModel):
    improved_body: str

@router.post("/improve-email", response_model=ImproveEmailResponse)
def improve_email(
    payload: ImproveEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Rewrite a sales email body for clarity, tone and grammar.
    Receives the raw body text, returns the improved version.
    Only the body text us sent to Haiku - no PII.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a professional B2B sales copywriter for the food distribution industry.

Rewrite the following email to make it:
- More professional and polished
- Concise and easy to read
- Warm but not pushy
- Correct any grammar or spelling errors
- Keep the same language as the original (French if French, English if English)
- Preserve all template variables like {{{{prospect.first_name}}}}, {{{{campaign.name}}}}, {{{{user.first_name}}}} exactly as-is

Return ONLY the rewritten email body — no explanation, no preamble.

Email to improve:
{payload.body}"""
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    improved = response.content[0].text.strip()
    return ImproveEmailResponse(improved_body=improved)