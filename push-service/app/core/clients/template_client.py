"""
Template Service Client

Fetches notification templates from the Template Service.
According to task: Template Service stores and manages notification templates,
handles variable substitution, supports multiple languages.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TemplateClient:
    """
    Client for fetching and rendering templates from Template Service.
    According to task: Template Service handles variable substitution.
    """

    def __init__(self):
        self.base_url = settings.TEMPLATE_SERVICE_URL
        self.timeout = settings.TEMPLATE_SERVICE_TIMEOUT
        self.use_dummy_templates = not self.base_url or settings.USE_DUMMY_TEMPLATES

        if self.use_dummy_templates:
            logger.warning(
                "Template service URL not configured. Using dummy templates. "
                "Set TEMPLATE_SERVICE_URL in .env to enable real template rendering."
            )

    async def render_template(
        self, template_code: str, variables: Dict[str, Any], language: Optional[str] = "en"
    ) -> Dict[str, str]:
        """
        Fetch and render notification template with variables.

        Args:
            template_code: Template identifier
            variables: Variables for substitution
            language: Language code (optional)

        Returns:
            Dict with 'title', 'body', and optionally 'image_url', 'click_action'
        """
        if self.use_dummy_templates:
            logger.debug(f"Using dummy template for {template_code}")
            return self._get_dummy_template(template_code, variables)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/templates/render",
                    json={
                        "template_code": template_code,
                        "variables": variables,
                        "language": language,
                        "channel": "push",
                    },
                )
                response.raise_for_status()

                data = response.json()
                rendered = data.get("data", {}).get("rendered", {})

                logger.info(f"Rendered template {template_code}")
                return {
                    "title": rendered.get("title", "Notification"),
                    "body": rendered.get("body", "You have a new notification"),
                    "image_url": rendered.get("image_url"),
                    "click_action": rendered.get("click_action"),
                }

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch template from template service: {str(e)}. "
                f"Falling back to dummy template."
            )
            return self._get_dummy_template(template_code, variables)
        except Exception as e:
            logger.error(
                f"Unexpected error fetching template: {str(e)}. Falling back to dummy template."
            )
            return self._get_dummy_template(template_code, variables)

    def _get_dummy_template(self, template_code: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate dummy template for testing.
        Simple variable substitution for common patterns.
        """
        # Extract common variables
        name = variables.get("name", "User")
        link = variables.get("link", "")

        # Basic templates based on template_code
        templates = {
            "welcome": {
                "title": f"Welcome {name}!",
                "body": f"Thanks for joining us, {name}. Get started now!",
                "click_action": str(link) if link else None,
            },
            "alert": {
                "title": "Alert",
                "body": f"Hello {name}, you have a new alert. Click to view.",
                "click_action": str(link) if link else None,
            },
            "reminder": {
                "title": "Reminder",
                "body": f"Hey {name}, don't forget!",
                "click_action": str(link) if link else None,
            },
        }

        # Return template or generic fallback
        return templates.get(
            template_code,
            {
                "title": f"Notification for {name}",
                "body": f"You have a new notification. Template: {template_code}",
                "click_action": str(link) if link else None,
            },
        )


# Global instance
template_client = TemplateClient()
