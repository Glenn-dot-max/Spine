"""
Advanded template renderer with variable substitution.
Supports nested variables, filters, and a safe rendering.
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

class AdvancesTemplateRenderer:
    """
    Template renderer with support for:
    - Nested variables: {{prospect.first_name}}
    - Filters: {{prospect.name|upper}}
    - Default values: {{prospect.first_name|default("Your Company")}}
    - Safe rendering (escapes undefined variables)
    """
    
    # Pattern pour détecter les variables {{xxx}}
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    @staticmethod
    def render(template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template: Template string with {{variables}}
            context: Dictionary with variable values
        
        Returns:
            Redenred string
        
        Example:
            >>> render("Hello {{prospect.first_name}}!", {"prospect": {"first_name": "John"}}})
            "Hello John!"
        """
        def replace_variable(match):
          var_expression = match.group(1).strip()
          return AdvancedTemplateRenderer._resolve_variable(var_expression, context)

        return AdvancedTemplateRenderer.VARIABLE_PATTERN.sub(replace_variable, template)

    @staticmethod
    def _resolve_variable(expression: str, context: Dict[str, Any]) -> str:
        """
        Resolve a variable expression.
        
        Supports: 
        - Simple: prospect.first_name
        - With filter: prospect.name|upper
        - With default: prospect.first_name|default("Your Company")
        """
        # Check for filter
        if '|' in expression:
            var_part, filter_part = expression.split('|', 1)
            var_path = var_part.strip()
            filters = filters.strip()
        else:
            var_path = expression.strip()
            filters = None

        # Resolve variable value
        value = AdvancesTemplateRenderer._get_nested_value(var_path, context)

        # Apply filters
        if filters:
            value = AdvancesTemplateRenderer._apply_filters(value, filters)

        return str(value) if value is not None else ""

    @staticmethod
    def _get_nested_value(path: str, context: Dict[str, Any]) -> Any:
        """
        Get value from nested dictionary.
        
        Example:
            path = "prospect.company.name"
            context = {"prospect": {"company": {"name": "Acme"}}}
            returns "Acme"
        """
        keys = path.split('.')
        value = context

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None  
            
            if value is None:
                return None

        return value

    @staticmethod
    def _apply_filters(value: Any, filters: str) -> Any:
        """
        Apply filters to a value.
        
        Supported filters:
        - upper: Convert to uppercase
        - lower: Convert to lowercase
        - capitalize: Capitalize first letter
        - default:"value": Use default if empty
        - dat_format:"%Y-%m-%d": Format datetime
        """
        filters = filter_expr.split('|')

        for f in filters:
            f = f.strip()

            # Filter: upper
            if f =='upper':
                value = str(value).upper() if value else value

            # Filter: lower
            elif f == 'lower':
                value = str(value).lower() if value else value

            # Filter: capitalize
            elif f == 'capitalize':
                value = str(value).capitalize() if value else value

            # Filter: default:"value"
            elif f.startswith('default:'):
                if not value:
                    default_value = f.split(':', 1)[1].strip('"\'')
                    if isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
                    if isinstance(value, datetime):
                        value = value.strftime(default_value)
                  
        return value

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """
        Extract variable names from a template.
        
        Args:
            template: Template string
        
        Returns:
            List of variable names

        Example:
            >>> extract_variables("Hello {{prospect.first_name}} from {{prospect.company.name}}!")
            ["prospect.first_name", "prospect.company.name"]
        """
        matches = AdvancesTemplateRenderer.VARIABLE_PATTERN.findall(template)
        variables = []

        for match in matches:
            # Remove filters and default values
            var_name = match.split('|')[0].strip()
            if var_name not in variables:
                variables.append(var_name)

        return variables

    @staticmethod
    def validate_template(template: str, required_context_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate that a template is well-formed and contains required variables.
        
        Args:
            template: Template string
            required_context_keys: List of required variable paths (e.g. ["prospect.first_name"])
        
        Returns:
            True if valid, False otherwise
        """
        variables = AdvancesTemplateRenderer.extract_variables(template)
        errors = []
        missing_keys = []

        if required_context_keys:
            top_level_keys = set(var.split('.')[0] for var in variables)
            for req_key in required_context_keys:
                if req_key not in top_level_keys:
                    missing_keys.append(req_key)
                    errors.append(f"Required context key '{req_key}' not used in template")

        if template.count('{{') != template.count('}}'):
            errors.append("Mismatched {{ and }} braces")

        return {
            "valid": len(errors) == 0,
            "variables": variables,
            "missing_keys": missing_keys,
            "errors": errors
        }

advanced_renderer = AdvancesTemplateRenderer()