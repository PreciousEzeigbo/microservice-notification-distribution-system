"""
Device Token Client

Fetches device tokens from the User Service.
When the service is unavailable, falls back to dummy tokens for testing.
"""

import logging
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeviceTokenClient:
    """
    Client for fetching device tokens from User Service.
    According to task: User Service manages user contact info (email, push tokens).
    """

    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = settings.USER_SERVICE_TIMEOUT
        self.use_dummy_tokens = not self.base_url or settings.USE_DUMMY_DEVICE_TOKENS

        if self.use_dummy_tokens:
            logger.warning(
                "User service URL not configured. Using dummy tokens. "
                "Set USER_SERVICE_URL in .env to enable real token lookup."
            )

    async def get_tokens_for_user(self, user_id: str, platform: Optional[str] = None) -> List[str]:
        """
        Fetch device tokens for a user.

        Args:
            user_id: User identifier
            platform: Optional platform filter (fcm, web_push, apns)

        Returns:
            List of device tokens
        """
        # Use dummy tokens if service is not configured
        if self.use_dummy_tokens:
            logger.debug(f"Using dummy tokens for user {user_id}")
            return self._get_dummy_tokens(user_id, platform)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call User Service to get user's push token
                response = await client.get(f"{self.base_url}/api/v1/users/{user_id}")
                response.raise_for_status()

                data = response.json()
                user_data = data.get("data", {})

                # Extract push_token from user data
                push_token = user_data.get("push_token")

                if not push_token:
                    logger.info(f"No push token found for user {user_id}")
                    return []

                tokens = [push_token]
                logger.info(f"Retrieved push token for user {user_id}")
                return tokens

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch tokens from device service: {str(e)}. "
                f"Falling back to dummy tokens."
            )
            return self._get_dummy_tokens(user_id, platform)
        except Exception as e:
            logger.error(
                f"Unexpected error fetching tokens: {str(e)}. Falling back to dummy tokens."
            )
            return self._get_dummy_tokens(user_id, platform)

    def _get_dummy_tokens(self, user_id: str, platform: Optional[str] = None) -> List[str]:
        """
        Generate dummy tokens for testing.

        In production, this should never be used.
        """
        # Generate consistent dummy tokens based on user_id for testing
        if platform == "web_push":
            return [f"dummy_web_push_token_{user_id}_1", f"dummy_web_push_token_{user_id}_2"]
        else:
            # Default to FCM tokens
            return [f"dummy_fcm_token_{user_id}_1", f"dummy_fcm_token_{user_id}_2"]

    async def validate_token(self, user_id: str) -> bool:
        """
        Check if user has a valid push token in User Service.

        Args:
            user_id: User identifier

        Returns:
            True if user has a push token, False otherwise
        """
        if self.use_dummy_tokens:
            return True

        try:
            tokens = await self.get_tokens_for_user(user_id)
            return len(tokens) > 0
        except Exception as e:
            logger.error(f"Token validation failed for user {user_id}: {str(e)}")
            return False

    async def invalidate_token(self, user_id: str):
        """
        Clear push token in User Service when it's invalid.

        Args:
            user_id: User identifier whose token should be cleared
        """
        if self.use_dummy_tokens:
            logger.debug(f"Skipping token invalidation (dummy mode): {user_id}")
            return

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Update user to clear push_token
                await client.patch(
                    f"{self.base_url}/api/v1/users/{user_id}", json={"push_token": None}
                )
                logger.info(f"Cleared push token for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to invalidate token for user {user_id}: {str(e)}")


# Global instance
device_token_client = DeviceTokenClient()
