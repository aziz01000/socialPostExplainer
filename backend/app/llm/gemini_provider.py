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
                    if 'embedding' in result:
                        embeddings.append(result['embedding'])
                        logger.debug(f"✓ Embedded text {i+1}/{len(texts)}")
                    else:
                        logger.warning(f"No embedding returned for text {i+1}")
                        embeddings.append([0.0] * 768)
                except Exception as e:
                    logger.error(f"Error embedding text {i+1}: {e}")
                    embeddings.append([0.0] * 768)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            # Return mock embeddings on error (1536-dim for compatibility with FAISS)
            embeddings = [[0.0] * 1536 for _ in texts]
        
        logger.info(f"✓ Generated {len(embeddings)} embedding(s)")
        return embeddings
    
    async def generate_chat_completion(self, messages: List[dict]) -> str:
        """Generate chat completion using Gemini."""
        if not self.client:
            error_msg = "Gemini client not initialized (missing API key)"
            logger.error(f"✗ {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # Get the last user message
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
            logger.info(f"✓ Chat completion generated successfully ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"✗ Gemini completion error: {e}", exc_info=True)
            raise
    
    async def check_moderation(self, text: str) -> dict:
        """Check text for safety using Gemini's safety filter."""
        # Gemini includes built-in safety filters
        # This is a placeholder - actual filtering happens server-side
        return {"flagged": False, "categories": {}}
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using Gemini's vision capabilities."""
        if not self.client:
            logger.warning("Gemini client not initialized - skipping image analysis")
            return "Image analysis unavailable (client not initialized)"
        
        try:
            logger.info(f"Analyzing image from URL: {image_url}")
            # For now, return a placeholder since vision API handling varies
            # Real implementation would need to handle image uploads properly
            logger.warning("Image analysis not available in current Gemini SDK version")
            return "Image analysis not available in current API version"
        except Exception as e:
            logger.error(f"✗ Image analysis error: {e}", exc_info=True)
            raise
