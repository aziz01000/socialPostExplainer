"""Google Gemini API integration."""

import logging
from google import genai
from typing import Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Google Gemini API client."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key if hasattr(settings, 'gemini_api_key') and settings.gemini_api_key else None
        self.model = settings.gemini_model
        self.base_url = settings.gemini_base_url
        self.client = None
        
        logger.info(f"Initializing Gemini provider with model: {self.model}")
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("✓ Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Gemini client: {e}")
        else:
            logger.warning("Gemini API key not set - client unavailable")
    
    async def generate_embeddings(self, texts: List[str], model: str = "gemini-embedding-001") -> List[List[float]]:
        """Generate embeddings for texts using Gemini."""
        if not texts or not self.client:
            logger.warning("No texts provided or client not initialized for embeddings")
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} text(s) using model: {model}")
        embeddings = []
        try:
            for i, text in enumerate(texts):
                try:
                    result = self.client.models.embed_content(
                        model=model,
                        contents=text
                    )
                    
                    # Handle different response structures from Gemini API
                    embedding = None
                    if isinstance(result, dict):
                        # Try different possible keys in response
                        if 'embedding' in result:
                            embedding = result['embedding']
                        elif 'embeddings' in result and len(result['embeddings']) > 0:
                            embedding = result['embeddings'][0].get('values', result['embeddings'][0])
                        else:
                            # Log full response for debugging
                            logger.debug(f"Response structure for text {i+1}: {result.keys() if isinstance(result, dict) else type(result)}")
                    else:
                        # Result might be an object with attributes
                        if hasattr(result, 'embedding'):
                            embedding = result.embedding
                        elif hasattr(result, 'embeddings') and len(result.embeddings) > 0:
                            embedding = result.embeddings[0]
                            if hasattr(embedding, 'values'):
                                embedding = embedding.values
                    
                    if embedding:
                        embeddings.append(embedding)
                        logger.debug(f"✓ Embedded text {i+1}/{len(texts)} (dim: {len(embedding)})")
                    else:
                        logger.error(f"✗ No embedding returned for text {i+1} - response keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
                        # Don't add fake embeddings - fail instead
                        raise ValueError(f"No embedding found in response for text {i+1}")
                except Exception as e:
                    logger.error(f"✗ Error embedding text {i+1}: {e}")
                    raise
        except Exception as e:
            logger.error(f"✗ Embedding error: {e}")
            raise
        
        logger.info(f"✓ Generated {len(embeddings)} embedding(s) successfully")
        return embeddings
    
    async def generate_chat_completion(self, messages: List[dict]) -> tuple[str, dict]:
        """Generate chat completion using Gemini. Returns (content, usage_dict)."""
        if not self.client:
            error_msg = "Gemini client not initialized (missing API key)"
            logger.error(f"✗ {error_msg}")
            raise ValueError(error_msg)
        usage_out = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        try:
            user_message = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break
            if not user_message:
                logger.error("No user message found in conversation")
                raise ValueError("No user message found")
            logger.info(f"Generating chat completion with {self.model}")
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_message
            )
            result = response.text if response.text else "No response generated"
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                usage_out = {
                    "prompt_tokens": getattr(um, "prompt_token_count", None) or getattr(um, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(um, "candidates_token_count", None) or getattr(um, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(um, "total_token_count", None) or 0,
                }
                if not usage_out["total_tokens"]:
                    usage_out["total_tokens"] = usage_out["prompt_tokens"] + usage_out["completion_tokens"]
            logger.info(f"✓ Chat completion generated successfully ({len(result)} chars, {usage_out.get('total_tokens', 0)} tokens)")
            return result, usage_out
        except Exception as e:
            logger.error(f"✗ Gemini completion error: {e}", exc_info=True)
            raise
    
    async def check_moderation(self, text: str) -> dict:
        """Check text for safety using Gemini's safety filter."""
        # Gemini includes built-in safety filters
        # This is a placeholder - actual filtering happens server-side
        return {"flagged": False, "categories": {}}
    
    async def analyze_image(self, image_url: str, question: str) -> tuple[str, dict]:
        """Analyze image using Gemini's vision capabilities. Returns (content, usage_dict)."""
        if not self.client:
            logger.warning("Gemini client not initialized - skipping image analysis")
            return "Image analysis unavailable (client not initialized)", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        try:
            logger.info(f"Analyzing image from URL: {image_url}")
            logger.warning("Image analysis not available in current Gemini SDK version")
            return "Image analysis not available in current API version", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        except Exception as e:
            logger.error(f"✗ Image analysis error: {e}", exc_info=True)
            raise
