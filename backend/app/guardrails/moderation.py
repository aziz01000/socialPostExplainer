"""Content moderation guardrails."""

from app.llm.model_router import ModelRouter
from app.config import settings


class ModerationGuardrail:
    """Content moderation using configured LLM provider."""
    
    def __init__(self):
        self.model_router = ModelRouter()
        # Disable moderation if using Gemini (Gemini has built-in safety)
        # Only enable for OpenAI
        self.enabled = settings.enable_input_moderation and settings.llm_provider == "openai"
    
    async def check_input(self, text: str) -> dict:
        """Check input text for policy violations.
        
        Returns dict with 'flagged' and 'categories' keys.
        """
        if not self.enabled:
            return {"flagged": False, "categories": {}}
        
        try:
            result = await self.model_router.check_moderation(text)
            return result
        except Exception as e:
            print(f"Moderation check failed, allowing: {e}")
            return {"flagged": False, "categories": {}}
    
    async def check_output(self, text: str) -> dict:
        """Check generated output for policy violations."""
        if not settings.enable_output_moderation or settings.llm_provider != "openai":
            return {"flagged": False, "categories": {}}
        
        try:
            result = await self.model_router.check_moderation(text)
            return result
        except Exception as e:
            print(f"Output moderation check failed, allowing: {e}")
            return {"flagged": False, "categories": {}}
