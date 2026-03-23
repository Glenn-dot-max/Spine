"""
Seed default email templates into the database.
Run this once to create global templates.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal
from app.models.email_template import EmailTemplate

def seed_default_templates():
    """Create default global templates."""
    db = SessionLocal()
    
    try:
        # Template 1: Initial email
        initial_template = EmailTemplate(
            user_id=None,  # Global template
            name="initial",
            category="campaign",
            subject_template="Great meeting you at {{campaign.name}}!",
            body_template="""
<p>Hi {{prospect.first_name}},</p>

<p>It was great meeting you at <strong>{{campaign.name}}</strong> in {{campaign.location}}!</p>

<p>I wanted to follow up on our conversation about {{prospect.company_name|default:"your company"}}.</p>

<p>As discussed, I'd love to continue our discussion and explore how we can help you.</p>

<p>Would you be available for a quick call this week?</p>

<p>Best regards,<br>
{{user.first_name}} {{user.last_name}}</p>
""",
            variables={"used_variables": ["campaign.name", "campaign.location", "prospect.first_name", "prospect.company_name", "user.first_name", "user.last_name"]},
            is_active=True,
            is_default=True
        )
        
        # Template 2: Follow-up 1
        followup1_template = EmailTemplate(
            user_id=None,
            name="followup_1",
            category="campaign",
            subject_template="Re: Great meeting you at {{campaign.name}}!",
            body_template="""
<p>Hi {{prospect.first_name}},</p>

<p>I wanted to follow up on my previous email about our meeting at {{campaign.name}}.</p>

<p>I know you're busy, but I'd really appreciate the opportunity to discuss how we can support {{prospect.company_name|default:"your business"}}.</p>

<p>Do you have 15 minutes this week for a quick call?</p>

<p>Looking forward to hearing from you!</p>

<p>Best regards,<br>
{{user.first_name}} {{user.last_name}}</p>
""",
            variables={"used_variables": ["prospect.first_name", "campaign.name", "prospect.company_name", "user.first_name", "user.last_name"]},
            is_active=True,
            is_default=True
        )
        
        # Template 3: Follow-up 2
        followup2_template = EmailTemplate(
            user_id=None,
            name="followup_2",
            category="campaign",
            subject_template="Re: Great meeting you at {{campaign.name}}!",
            body_template="""
<p>Hi {{prospect.first_name}},</p>

<p>I hope this email finds you well!</p>

<p>I wanted to reach out one more time about our conversation at {{campaign.name}}.</p>

<p>If now isn't a good time, no worries at all. Feel free to reach out whenever you're ready to continue the discussion.</p>

<p>In the meantime, here's my direct contact information if you need anything:</p>
<p>Email: {{user.email|default:"contact@company.com"}}<br>
Phone: [Your phone number]</p>

<p>Thanks again for your time at the show!</p>

<p>Best regards,<br>
{{user.first_name}} {{user.last_name}}</p>
""",
            variables={"used_variables": ["prospect.first_name", "campaign.name", "user.first_name", "user.last_name", "user.email"]},
            is_active=True,
            is_default=True
        )
        
        # Template 4: Follow-up 3 (final)
        followup3_template = EmailTemplate(
            user_id=None,
            name="followup_3",
            category="campaign",
            subject_template="Re: Great meeting you at {{campaign.name}}!",
            body_template="""
<p>Hi {{prospect.first_name}},</p>

<p>I don't want to fill up your inbox, so this will be my last follow-up email.</p>

<p>It was truly a pleasure meeting you at {{campaign.name}}, and I hope we can work together in the future.</p>

<p>If you ever need anything or want to revisit our conversation, please don't hesitate to reach out. My door is always open!</p>

<p>Wishing you and {{prospect.company_name|default:"your team"}} all the best.</p>

<p>Warm regards,<br>
{{user.first_name}} {{user.last_name}}</p>
""",
            variables={"used_variables": ["prospect.first_name", "campaign.name", "prospect.company_name", "user.first_name", "user.last_name"]},
            is_active=True,
            is_default=True
        )
        
        # Check if templates already exist
        existing = db.query(EmailTemplate).filter(EmailTemplate.user_id == None).count()
        
        if existing > 0:
            print(f"⚠️  {existing} global templates already exist. Skipping seed.")
            return
        
        # Add templates
        db.add(initial_template)
        db.add(followup1_template)
        db.add(followup2_template)
        db.add(followup3_template)
        
        db.commit()
        
        print("✅ Successfully seeded 4 default email templates!")
        print("   - initial")
        print("   - followup_1")
        print("   - followup_2")
        print("   - followup_3")
        
    except Exception as e:
        print(f"❌ Error seeding templates: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding default email templates...")
    seed_default_templates()