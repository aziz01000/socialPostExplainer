"""Content moderation guardrails."""

from app.llm.model_router import ModelRouter
from app.config import settings


class ModerationGuardrail:
    """OpenAI moderation API wrapper."""
    
    def __init__(self):
        self.model_router = ModelRouter()
        self.enabled = settings.enable_input_moderation
    
    async def check_input(self, text: str) -> dict:
        """Check input text for policy violations.
        
        Returns dict with 'flagged' and 'categories' keys.
        """
        if not self.enabled:
            return {"flagged": False, "categories": {}}
        
        result = await self.model_router.check_moderation(text)
        return result
    
    async def check_output(self, text: str) -> dict:
        """Check generated output for policy violations."""
        if not settings.enable_output_moderation:
            return {"flagged": False, "categories": {}}
        
        result = await self.model_router.check_moderation(text)
        return result
