"""
Email template renderer using Jinja2.
Loads HTML templates and renders them with provided data.
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from pathlib import Path
from typing import Dict, Any

# Get the templates directory path
# This finds: backend/app/templates/emails/
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "emails"


class EmailTemplateRenderer:
    """
    Renders email templates with dynamic data.
    
    Example usage:
        renderer = EmailTemplateRenderer()
        html = renderer.render(
            template_name="campaigns/initial.html",
            data={
                "first_name": "John",
                "campaign_name": "Show Chefs LA 2026"
            }
        )
    """
    
    def __init__(self):
        """Initialize Jinja2 environment with templates folder."""
        # Create Jinja2 environment
        # FileSystemLoader = load templates from disk
        # autoescape = prevent XSS attacks in HTML
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def render(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Render a template with provided data.
        
        Args:
            template_name: Path to template (e.g., "campaigns/initial.html")
            data: Dictionary of variables to inject into template
                  Example: {"first_name": "John", "campaign_name": "Show XYZ"}
        
        Returns:
            Rendered HTML string with variables replaced
        
        Raises:
            TemplateNotFound: If template file doesn't exist
            Exception: If rendering fails
        """
        try:
            # Load the template file
            template = self.env.get_template(template_name)
            
            # Render with data (replaces {{variables}})
            html = template.render(**data)
            
            return html
            
        except TemplateNotFound:
            raise FileNotFoundError(f"Email template not found: {template_name}")
        except Exception as e:
            raise Exception(f"Error rendering template {template_name}: {str(e)}")
    
    def render_campaign_email(
        self,
        template_name: str,
        prospect_first_name: str,
        prospect_last_name: str,
        prospect_company: str,
        campaign_name: str,
        campaign_location: str = None,
        sender_name: str = "The Team",
        **extra_vars
    ) -> str:
        """
        Convenience method for rendering campaign emails.
        Pre-fills common variables.
        
        Args:
            template_name: Which template to use ("initial.html", "followup_1.html", etc.)
            prospect_first_name: Contact's first name
            prospect_last_name: Contact's last name
            prospect_company: Contact's company
            campaign_name: Trade show name
            campaign_location: Trade show location (optional)
            sender_name: Your name
            **extra_vars: Any additional variables for the template
        
        Returns:
            Rendered HTML email
        """
        # Build full path: campaigns/initial.html
        full_template_path = f"campaigns/{template_name}"
        
        # Prepare data dictionary
        data = {
            "first_name": prospect_first_name,
            "last_name": prospect_last_name,
            "company_name": prospect_company,
            "campaign_name": campaign_name,
            "campaign_location": campaign_location,
            "sender_name": sender_name,
            **extra_vars  # Add any extra variables
        }
        
        return self.render(full_template_path, data)


# Create singleton instance (reuse across app)
email_renderer = EmailTemplateRenderer()