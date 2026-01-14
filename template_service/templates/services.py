import re
from pybars import Compiler
from typing import Dict, Set, Any
from django.core.exceptions import ValidationError

# Initialize PyBars compiler
compiler = Compiler()

def extract_placeholders(template_content: str) -> Set[str]:
    """
    Extract all {{variable}} and {{{triple}}} placeholders from template content.
    Returns a set of variable names found in the template.
    """
    pattern = r'{{{?\s*([a-zA-Z0-9_\.]+)\s*}}}'
    return {match.group(1) for match in re.finditer(pattern, template_content)}

def compile_template(html_body: str, text_body: str | None, variables: Dict[str, Any]) -> Dict[str, str | None]:
    """
    Compile template with provided variables using PyBars.
    Returns a dictionary with compiled HTML and text (if provided).
    """
    # Compile HTML
    template_html = compiler.compile(html_body)
    compiled_html = template_html(variables)

    # Compile text if provided
    compiled_text = None
    if text_body:
        template_text = compiler.compile(text_body)
        compiled_text = template_text(variables)

    return {
        "html": compiled_html,
        "text": compiled_text
    }

def validate_required_variables(template: 'Template', provided_vars: Dict[str, Any]) -> None:
    """
    Validate that all required template variables are provided.
    Raises ValidationError if any required variables are missing.
    """
    # Extract placeholders from both HTML and text bodies
    required_vars = extract_placeholders(template.html_body)
    if template.text_body:
        required_vars.update(extract_placeholders(template.text_body))

    # Check for missing variables
    missing_vars = required_vars - provided_vars.keys()
    if missing_vars:
        raise ValidationError(
            f"Missing required template variables: {', '.join(sorted(missing_vars))}",
            code='missing_template_variables'
        )