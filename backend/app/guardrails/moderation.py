"""Guardrails using OpenAI moderation API."""

import logging
import time
from typing import Optional

import httpx
from app.config import settings
from app.observability import tracer

logger = logging.getLogger(__name__)


class ModerationClient:
    """Client for OpenAI moderation API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize moderation client.

        Args:
            api_key: OpenAI API key (defaults to setting)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.endpoint = "https://api.openai.com/v1/moderations"
        self.enabled = settings.ENABLE_INPUT_MODERATION or settings.ENABLE_OUTPUT_MODERATION

    async def check_input(self, text: str) -> tuple[bool, dict]:
        """Check input text for policy violations.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_safe, flagged_categories)
        """
        if not settings.ENABLE_INPUT_MODERATION or not self.enabled:
            return True, {}

        return await self._check_text(text, "input")

    async def check_output(self, text: str) -> tuple[bool, dict]:
        """Check output text for policy violations.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_safe, flagged_categories)
        """
        if not settings.ENABLE_OUTPUT_MODERATION or not self.enabled:
            return True, {}

        return await self._check_text(text, "output")

    async def _check_text(self, text: str, check_type: str) -> tuple[bool, dict]:
        """Check text using OpenAI moderation API.

        Args:
            text: Text to check
            check_type: Type of check (input/output)

        Returns:
            Tuple of (is_safe, flagged_categories)
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": text},
                    timeout=10.0,
                )

            if response.status_code != 200:
                logger.error(
                    f"Moderation API error: {response.status_code} - {response.text}"
                )
                # Fail open - allow content if API fails
                return True, {}

            data = response.json()
            results = data.get("results", [])[0]

            flagged = results.get("flagged", False)
            categories = results.get("categories", {})
            flagged_categories = {k: v for k, v in categories.items() if v}

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_moderation(check_type, text, flagged, flagged_categories, latency_ms)

            if flagged:
                logger.warning(f"Content flagged in {check_type}: {flagged_categories}")

            return not flagged, flagged_categories

        except Exception as e:
            logger.error(f"Moderation check failed: {str(e)}")
            # Fail open
            return True, {}


def create_moderation_response(flagged_categories: dict) -> str:
    """Create a safe response for flagged content.

    Args:
        flagged_categories: Dictionary of flagged categories

    Returns:
        Safe error message
    """
    return (
        "I can't provide an explanation for this content as it may violate content policies. "
        "Please try with different content."
    )


# Global moderation client
moderation_client = ModerationClient()
