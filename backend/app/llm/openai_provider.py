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
        """Analyze image using vision model."""
        logger.info(f"Analyzing image from URL: {image_url}")
        
        # Try vision models in order of capability
        # gpt-4o supports vision, gpt-4-turbo is fallback, then use configured model
        vision_models_to_try = []
        
        # Try common vision models first
        if self.model in ["gpt-4o-mini", "gpt-4o"]:
            vision_models_to_try.append(self.model)
        
        # Add additional vision models
        vision_models_to_try.extend(["gpt-4-turbo", "gpt-4-vision-preview"])
        
        # Fall back to configured model if different
        if self.model not in vision_models_to_try:
            vision_models_to_try.append(self.model)
        
        last_error = None
        
        for model in vision_models_to_try:
            url = f"{self.base_url}/chat/completions"
            
            # Ensure URL is properly formatted
            if not isinstance(image_url, str) or not (image_url.startswith('http://') or image_url.startswith('https://')):
                error_msg = f"Invalid image URL: {image_url}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": question
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1024,
            }
            
            try:
                logger.debug(f"Attempting image analysis with model: {model}")
                response = await self.client.post(url, json=payload)
                
                # Log response status
                logger.debug(f"Image analysis response status: {response.status_code}")
                
                response.raise_for_status()
                data = response.json()
                result = data["choices"][0]["message"]["content"]
                logger.info(f"✓ Image analysis completed with {model} ({len(result)} chars)")
                return result
                
            except httpx.HTTPStatusError as e:
                # Try to extract error details from response
                error_detail = f"HTTP {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if "error" in error_data:
                        error_detail = f"{error_detail}: {error_data['error'].get('message', str(error_data['error']))}"
                    else:
                        error_detail = f"{error_detail}: {str(error_data)}"
                except:
                    error_detail = f"{error_detail}: {e.response.text[:200]}"
                
                logger.warning(f"Model '{model}' failed: {error_detail}")
                last_error = error_detail
                
                # Try next model on 400/401/403/429 errors
                if e.response.status_code in [400, 401, 403, 429]:
                    if model != vision_models_to_try[-1]:
                        logger.debug(f"Trying fallback model: {vision_models_to_try[vision_models_to_try.index(model) + 1]}")
                        continue
                    else:
                        # All models failed
                        logger.error(f"✗ Image analysis failed with all vision models. Last error: {error_detail}")
                        raise ValueError(f"Image analysis not available: {error_detail}")
                else:
                    # For other errors, fail immediately
                    raise
                    
            except Exception as e:
                logger.error(f"✗ Image analysis error with model '{model}': {e}", exc_info=True)
                last_error = str(e)
                if model == vision_models_to_try[-1]:
                    raise
                continue
        
        # Fallback error
        raise ValueError(f"Image analysis failed: {last_error}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
