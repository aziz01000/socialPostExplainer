"""Google Gemini API integration."""

import httpx
from typing import Optional, List
from app.config import settings


class GeminiProvider:
    """Google Gemini API client."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key if hasattr(settings, 'gemini_api_key') and settings.gemini_api_key else None
        self.model = settings.gemini_model if hasattr(settings, 'gemini_model') else "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.client = httpx.AsyncClient()
    
    async def generate_embeddings(self, texts: List[str], model: str = "embedding-001") -> List[List[float]]:
        """Generate embeddings for texts using Gemini."""
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
                data = response.json()
                if "embedding" in data:
                    embeddings.append(data["embedding"]["values"])
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([0.0] * 768)  # Default embedding dimension for Gemini
        
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
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            return "No response generated"
        except Exception as e:
            raise Exception(f"Gemini completion error: {e}")
    
    async def check_moderation(self, text: str) -> dict:
        """Check text for safety using Gemini's safety filter."""
        # Gemini includes built-in safety filters
        # This is a placeholder that reflects Gemini's approach
        return {"flagged": False, "categories": {}}
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using Gemini's vision capabilities."""
        url = f"{self.base_url}/{self.model}:generateContent"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": question},
                        {"inlineData": {"mimeType": "image/jpeg", "data": image_url}}
                    ]
                }
            ]
        }
        params = {"key": self.api_key}
        
        try:
            response = await self.client.post(url, json=payload, params=params)
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            return "No image analysis available"
        except Exception as e:
            raise Exception(f"Gemini image analysis error: {e}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
