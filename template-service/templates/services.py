import re
from pybars import Compiler
from typing import Dict, Set, Any
from django.core.exceptions import ValidationError

# Initialize PyBars compiler
compiler = Compiler()

# Handlebars control keywords and block helpers that should not be treated as variables
RESERVED_TAGS = {"else", "if", "each", "with", "unless", "log", "lookup", "block", "inline"}

def extract_placeholders(template_content: str) -> Set[str]:
    """
    Extract all {{variable}} and {{{triple}}} placeholders from template content.
    Returns a set of variable names found in the template.
    """
    pattern = r'{{{?\s*([a-zA-Z0-9_\.]+)\s*}}}?'
    return {
        match.group(1)
        for match in re.finditer(pattern, template_content or "")
        if match.group(1) not in RESERVED_TAGS
    }

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
    if text_body is not None:
        template_text = compiler.compile(text_body)
        compiled_text = template_text(variables)

    return {
        "html": compiled_html,
        "text": compiled_text
    }

def validate_required_variables(template: 'EmailTemplate', provided_vars: Dict[str, Any]) -> None:
    """
    Validate that all required template variables are provided.
    Raises ValidationError if any required variables are missing.
    """
    # Extract placeholders from both HTML and text bodies
    required_vars = extract_placeholders(template.html_content)
    required_vars.update(extract_placeholders(template.subject))
    if template.text_content:
        required_vars.update(extract_placeholders(template.text_content))

    # Check for missing variables
    missing_vars = []
    for var_path in required_vars:
        keys = var_path.split('.')
        current_level = provided_vars
        found = True
        for key in keys:
            if not isinstance(current_level, dict) or key not in current_level:
                found = False
                break
            current_level = current_level[key]
        if not found:
            missing_vars.append(var_path)

    if missing_vars:
        raise ValidationError(
            f"Missing required template variables: {', '.join(sorted(missing_vars))}",
            code='missing_template_variables'
        )
    