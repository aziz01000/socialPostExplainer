"""LLM provider factory and router."""

import logging
from typing import Literal, Optional

from app.config import settings
from app.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes LLM calls to the appropriate provider."""

    def __init__(
        self,
        default_provider: Literal["openai", "anthropic"] = "openai",
    ):
        """Initialize model router.

        Args:
            default_provider: Default LLM provider
        """
        self.default_provider = default_provider or settings.LLM_PROVIDER
        self.openai_provider = OpenAIProvider()
        # Anthropic provider would be initialized here in the future

    def get_provider(self, provider: Optional[str] = None):
        """Get the LLM provider.

        Args:
            provider: Optional provider override

        Returns:
            The LLM provider instance
        """
        provider = provider or self.default_provider

        if provider == "openai":
            return self.openai_provider

        logger.warning(f"Unknown provider {provider}, using OpenAI")
        return self.openai_provider

    async def generate_explanation(
        self,
        post: str,
        context: list[str],
        image_analysis: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> tuple[str, dict]:
        """Generate explanation using the selected provider.

        Args:
            post: The social media post
            context: List of context documents
            image_analysis: Optional image analysis
            provider: Optional provider override

        Returns:
            Tuple of (explanation, token_usage)
        """
        selected_provider = self.get_provider(provider)
        return await selected_provider.generate_explanation(
            post=post,
            context=context,
            image_analysis=image_analysis,
        )

    async def get_embeddings(
        self,
        texts: list[str],
        provider: Optional[str] = None,
    ) -> list[list[float]]:
        """Get embeddings using the selected provider.

        Args:
            texts: List of texts to embed
            provider: Optional provider override

        Returns:
            List of embedding vectors
        """
        selected_provider = self.get_provider(provider)
        return await selected_provider.get_embeddings(texts)

    async def analyze_image(
        self,
        image_url: str,
        post: str,
        provider: Optional[str] = None,
    ) -> Optional[str]:
        """Analyze image using the selected provider.

        Args:
            image_url: URL of the image
            post: Associated social media post
            provider: Optional provider override

        Returns:
            Image analysis or None
        """
        selected_provider = self.get_provider(provider)
        return await selected_provider.analyze_image(image_url=image_url, post=post)


# Global router instance
model_router = ModelRouter(default_provider=settings.LLM_PROVIDER)
