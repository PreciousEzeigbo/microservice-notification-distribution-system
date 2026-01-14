import re
from handlebars import Handlebars
from typing import Dict, Set

handlebars = Handlebars()

def extract_placeholders(template_content: str) -> Set[str]:
    """Extract all {{variable}} and {{{triple}}} from template"""
    pattern = r'{{{#?|\{\{\{)\s*([a-zA-Z0-9_\.]+)\s*}'
    return {match[1] for match in re.finditer(pattern, template_content)}

def compile_template(html_body: str, text_body: str | None, variables: Dict) -> Dict:
    compiled_html = handlebars.compile(html_body)(variables)
    
    compiled_text = None
    if text_body:
        compiled_text = handlebars.compile(text_body)(variables)
    
    return {
        "html": compiled_html,
        "text": compiled_text
    }

def validate_required_variables(template: 'Template', provided_vars: Dict) -> None:
    html_placeholders = extract_placeholders(template.html_body)
    if template.text_body:
        html_placeholders.update(extract_placeholders(template.text_body))
    
    missing = html_placeholders - provided_vars.keys()
    if missing:
        raise ValueError(f"Missing required template variables: {', '.join(sorted(missing))}")