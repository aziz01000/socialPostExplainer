"""OpenAI API integration."""

import httpx
import json
import logging
from typing import Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI API client."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = settings.openai_base_url
        
        logger.info(f"Initializing OpenAI provider with model: {self.model}")
        logger.info(f"Base URL: {self.base_url}")
        
        if not self.api_key:
            logger.error("✗ OpenAI API key not configured")
        else:
            logger.info("✓ OpenAI API key configured")
        
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Generate embeddings for texts."""
        if not texts:
            logger.warning("No texts provided for embedding")
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} text(s) using model: {model}")
        url = f"{self.base_url}/embeddings"
        payload = {
            "input": texts,
            "model": model,
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Sort by index to maintain order
            embeddings = sorted(data.get("data", []), key=lambda x: x["index"])
            logger.info(f"✓ Generated {len(embeddings)} embedding(s)")
            return [item["embedding"] for item in embeddings]
        except Exception as e:
            logger.error(f"✗ Embedding error: {e}", exc_info=True)
            raise
    
    async def generate_chat_completion(self, messages: List[dict]) -> str:
        """Generate chat completion."""
        logger.info(f"Generating chat completion with {self.model}")
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            logger.info(f"✓ Chat completion generated successfully ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"✗ Completion error: {e}", exc_info=True)
            raise
    
    async def check_moderation(self, text: str) -> dict:
        """Check text against moderation API."""
        logger.debug(f"Running moderation check on text ({len(text)} chars)")
        url = f"{self.base_url}/moderations"
        payload = {
            "input": text,
            "model": "text-moderation-latest",
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if results:
                result = results[0]
                flagged = result.get("flagged", False)
                logger.info(f"✓ Moderation check complete (flagged: {flagged})")
                return {
                    "flagged": flagged,
                    "categories": result.get("categories", {})
                }
            logger.warning("No moderation results returned")
            return {"flagged": False, "categories": {}}
        except Exception as e:
            logger.error(f"✗ Moderation error (failing open): {e}", exc_info=True)
            # Fail open - don't block on moderation errors
            return {"flagged": False, "categories": {}}
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using GPT-4o vision."""
        logger.info(f"Analyzing image from URL: {image_url}")
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 1024,
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            logger.info(f"✓ Image analysis completed ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"✗ Image analysis error: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
