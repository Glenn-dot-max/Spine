"""
Advanced template renderer with variable substitution.
Supports nested variables, filters, and safe rendering.
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class AdvancedTemplateRenderer:
    """
    Template renderer with support for:
    - Nested variables: {{prospect.first_name}}
    - Filters: {{prospect.name|upper}}
    - Default values: {{prospect.company_name|default:"Your Company"}}
    - Safe rendering (escapes undefined variables)
    """
    
    # Pattern to detect {{xxx}} variables
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    @staticmethod
    def render(template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template: Template string with {{variables}}
            context: Dictionary with variable values
        
        Returns:
            Rendered string
        
        Example:
            >>> render("Hello {{prospect.first_name}}!", {"prospect": {"first_name": "John"}})
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
        - With default: prospect.company_name|default:"Your Company"
        """
        # Check for filter
        if '|' in expression:
            var_part, filter_part = expression.split('|', 1)
            var_path = var_part.strip()
            filter_part = filter_part.strip()
        else:
            var_path = expression.strip()
            filter_part = None

        # Resolve variable value
        value = AdvancedTemplateRenderer._get_nested_value(var_path, context)

        # Apply filters
        if filter_part:
            value = AdvancedTemplateRenderer._apply_filters(value, filter_part)

        return str(value) if value is not None else ""

    @staticmethod
    def _get_nested_value(path: str, context: Dict[str, Any]) -> Any:
        """
        Get value from nested dictionary.
        
        Example:
            path = "prospect.company_name"
            context = {"prospect": {"company_name": "Acme"}}
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
    def _apply_filters(value: Any, filter_expr: str) -> Any:
        """
        Apply filters to a value.
        
        Supported filters:
        - upper: Convert to uppercase
        - lower: Convert to lowercase
        - capitalize: Capitalize first letter
        - default:"value": Use default if empty
        """
        filter_list = filter_expr.split('|')

        for f in filter_list:
            f = f.strip()

            # Filter: upper
            if f == 'upper':
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
                    value = default_value
                  
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
            >>> extract_variables("Hello {{prospect.first_name}} from {{prospect.company_name}}!")
            ["prospect.first_name", "prospect.company_name"]
        """
        matches = AdvancedTemplateRenderer.VARIABLE_PATTERN.findall(template)
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
            required_context_keys: List of required variable paths (e.g. ["prospect", "campaign"])
        
        Returns:
            Dictionary with validation results
        """
        variables = AdvancedTemplateRenderer.extract_variables(template)
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


# Create singleton instance
advanced_renderer = AdvancedTemplateRenderer()