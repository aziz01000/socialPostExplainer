"""Google Gemini API integration."""

import httpx
import base64
from typing import Optional, List
from app.config import settings


class GeminiProvider:
    """Google Gemini API client."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key if hasattr(settings, 'gemini_api_key') and settings.gemini_api_key else None
        self.model = settings.gemini_model if hasattr(settings, 'gemini_model') else "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.client = httpx.AsyncClient()
    
    async def generate_embeddings(self, texts: List[str], model: str = "text-embedding-004") -> List[List[float]]:
        """Generate embeddings for texts using Gemini."""
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            url = f"{self.base_url}/{model}:embedContent"
            payload = {
                "model": f"models/{model}",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            params = {"key": self.api_key}
            
            try:
                response = await self.client.post(url, json=payload, params=params)
                response.raise_for_status()
                data = response.json()
                if "embedding" in data:
                    embeddings.append(data["embedding"]["values"])
                else:
                    embeddings.append([0.0] * 768)
            except Exception as e:
                print(f"Embedding error for text: {e}")
                embeddings.append([0.0] * 768)
        
        return embeddings
    
    async def generate_chat_completion(self, messages: List[dict]) -> str:
        """Generate chat completion using Gemini."""
        url = f"{self.base_url}/{self.model}:generateContent"
        
        # Convert messages format to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
        }
        params = {"key": self.api_key}
        
        try:
            response = await self.client.post(url, json=payload, params=params)
            response.raise_for_status()
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0].get("text", "")
                return content if content else "No response generated"
            return "No response generated"
        except Exception as e:
            print(f"Gemini completion error: {e}")
            raise
    
    async def check_moderation(self, text: str) -> dict:
        """Check text for safety using Gemini's safety filter."""
        # Gemini includes built-in safety filters
        # This is a placeholder - actual filtering happens server-side
        return {"flagged": False, "categories": {}}
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using Gemini's vision capabilities."""
        url = f"{self.base_url}/{self.model}:generateContent"
        
        # For URL-based images, use direct URL
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": question},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": image_url  # Gemini handles URL directly
                            }
                        }
                    ]
                }
            ]
        }
        params = {"key": self.api_key}
        
        try:
            response = await self.client.post(url, json=payload, params=params)
            response.raise_for_status()
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0].get("text", "")
                return content if content else "No image analysis available"
            return "No image analysis available"
        except Exception as e:
            print(f"Gemini image analysis error: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
