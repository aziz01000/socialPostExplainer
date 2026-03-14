"""LLM model routing."""

from app.config import settings
from app.llm.openai_provider import OpenAIProvider


class ModelRouter:
    """Route LLM calls to appropriate provider."""
    
    def __init__(self):
        if settings.llm_provider == "openai":
            self.provider = OpenAIProvider()
        elif settings.llm_provider == "gemini":
            from app.llm.gemini_provider import GeminiProvider
            self.provider = GeminiProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    async def generate_embeddings(self, texts: list) -> list:
        """Generate embeddings."""
        return await self.provider.generate_embeddings(texts)
    
    async def generate_completion(self, messages: list) -> str:
        """Generate completion."""
        return await self.provider.generate_chat_completion(messages)
    
    async def check_moderation(self, text: str) -> dict:
        """Check moderation."""
        return await self.provider.check_moderation(text)
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image."""
        return await self.provider.analyze_image(image_url, question)
