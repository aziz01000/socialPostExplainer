"""OpenAI API integration."""

import httpx
import json
from typing import Optional, List
from app.config import settings


class OpenAIProvider:
    """OpenAI API client."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Generate embeddings for texts."""
        if not texts:
            return []
        
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
            return [item["embedding"] for item in embeddings]
        except Exception as e:
            print(f"Embedding error: {e}")
            raise
    
    async def generate_chat_completion(self, messages: List[dict]) -> str:
        """Generate chat completion."""
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
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Completion error: {e}")
            raise
    
    async def check_moderation(self, text: str) -> dict:
        """Check text against moderation API."""
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
                return {
                    "flagged": result.get("flagged", False),
                    "categories": result.get("categories", {})
                }
            return {"flagged": False, "categories": {}}
        except Exception as e:
            print(f"Moderation error: {e}")
            # Fail open - don't block on moderation errors
            return {"flagged": False, "categories": {}}
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using GPT-4o vision."""
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
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Image analysis error: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
