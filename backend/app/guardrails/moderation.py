"""Content moderation guardrails."""

import logging
from app.llm.model_router import ModelRouter
from app.config import settings

logger = logging.getLogger(__name__)


class ModerationGuardrail:
    """Content moderation using configured LLM provider."""
    
    # Flagged categories
    BLOCKED_CATEGORIES = {
        "hate",
        "violence",
        "sexual",
        "harassment",
        "self-harm",
        "illegal",
        "criminal",
        "jailbreak",
        "malware",
        "nsfw"
    }
    
    # Keywords to detect problematic content
    JAILBREAK_KEYWORDS = [
        "ignore your instructions",
        "pretend you are",
        "forget", "previous instructions",
        "system prompt",
        "bypass", "circumvent",
        "ignore safety",
        "ignore moderation",
        "act as an unfiltered",
        "without any restrictions"
    ]
    
    VIOLENCE_KEYWORDS = [
        "kill", "murder", "attack", "assault", "bomb", "shoot",
        "torture", "rape", "abuse", "brutal", "violent"
    ]
    
    HATE_KEYWORDS = [
        "racist", "sexist", "homophobic", "Nazi", "hate group",
        "inferior", "subhuman", "slur"
    ]
    
    CRIME_KEYWORDS = [
        "steal", "robbery", "fraud", "cocaine", "heroin", "drugs",
        "illegal", "criminal", "launder", "counterfeit"
    ]
    
    def __init__(self):
        self.model_router = ModelRouter()
        self.enabled = settings.enable_input_moderation
        logger.info(f"ModerationGuardrail initialized (enabled={self.enabled})")
    
    async def check_input(self, text: str) -> dict:
        """Check input text for policy violations.
        
        Returns dict with 'flagged', 'reason', and 'category' keys.
        """
        if not self.enabled or not text:
            return {"flagged": False, "reason": None, "category": None}
        
        # Local keyword checks (fast, always active)
        local_result = self._check_keywords(text)
        if local_result["flagged"]:
            logger.warning(f"✗ Input blocked (local): {local_result['category']} - {local_result['reason']}")
            return local_result
        
        # Provider-based checks
        if settings.llm_provider.lower() == "openai":
            try:
                result = await self.model_router.check_moderation(text)
                if result.get("flagged"):
                    logger.warning(f"✗ Input blocked (OpenAI): {result.get('categories', {})}")
                    return {
                        "flagged": True,
                        "reason": f"Content violates policy: {list(result.get('categories', {}).keys())}",
                        "category": list(result.get("categories", {}).keys())[0] if result.get("categories") else "policy_violation"
                    }
            except Exception as e:
                logger.error(f"OpenAI moderation check failed: {e}")
                # Fail open on error
                return {"flagged": False, "reason": None, "category": None}
        
        logger.info(f"✓ Input passed moderation check")
        return {"flagged": False, "reason": None, "category": None}
    
    async def check_output(self, text: str) -> dict:
        """Check generated output for policy violations."""
        if not settings.enable_output_moderation or not text:
            return {"flagged": False, "reason": None, "category": None}
        
        # Local keyword checks
        local_result = self._check_keywords(text)
        if local_result["flagged"]:
            logger.warning(f"✗ Output blocked (local): {local_result['category']} - {local_result['reason']}")
            return local_result
        
        # Provider-based checks
        if settings.llm_provider.lower() == "openai":
            try:
                result = await self.model_router.check_moderation(text)
                if result.get("flagged"):
                    logger.warning(f"✗ Output blocked (OpenAI): {result.get('categories', {})}")
                    return {
                        "flagged": True,
                        "reason": f"Generated content violates policy: {list(result.get('categories', {}).keys())}",
                        "category": list(result.get("categories", {}).keys())[0] if result.get("categories") else "policy_violation"
                    }
            except Exception as e:
                logger.error(f"OpenAI output moderation check failed: {e}")
                return {"flagged": False, "reason": None, "category": None}
        
        logger.info(f"✓ Output passed moderation check")
        return {"flagged": False, "reason": None, "category": None}
    
    def _check_keywords(self, text: str) -> dict:
        """Local keyword-based content check."""
        text_lower = text.lower()
        
        # Check for jailbreak attempts
        for keyword in self.JAILBREAK_KEYWORDS:
            if keyword.lower() in text_lower:
                return {
                    "flagged": True,
                    "reason": f"Potential jailbreak attempt detected: '{keyword}'",
                    "category": "jailbreak"
                }
        
        # Check for violence
        for keyword in self.VIOLENCE_KEYWORDS:
            if keyword.lower() in text_lower:
                return {
                    "flagged": True,
                    "reason": f"Violent content detected: '{keyword}'",
                    "category": "violence"
                }
        
        # Check for hate speech
        for keyword in self.HATE_KEYWORDS:
            if keyword.lower() in text_lower:
                return {
                    "flagged": True,
                    "reason": f"Hate speech detected: '{keyword}'",
                    "category": "hate"
                }
        
        # Check for crime-related content
        for keyword in self.CRIME_KEYWORDS:
            if keyword.lower() in text_lower:
                return {
                    "flagged": True,
                    "reason": f"Illegal/criminal content detected: '{keyword}'",
                    "category": "criminal"
                }
        
        return {"flagged": False, "reason": None, "category": None}
