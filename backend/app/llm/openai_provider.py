"""OpenAI LLM provider."""

import base64
import io
import logging
import time
from typing import Optional

import httpx
from app.config import settings
from app.observability import tracer

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI LLM provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to setting)
            model: Model name (defaults to setting)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.chat_endpoint = "https://api.openai.com/v1/chat/completions"
        self.embedding_endpoint = "https://api.openai.com/v1/embeddings"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def generate_explanation(
        self,
        post: str,
        context: list[str],
        image_analysis: Optional[str] = None,
    ) -> tuple[str, dict]:
        """Generate explanation for a post using context.

        Args:
            post: The social media post
            context: List of relevant context documents
            image_analysis: Optional image analysis to include

        Returns:
            Tuple of (explanation, token_usage)
        """
        start_time = time.time()

        # Build the prompt
        context_str = "\n\n".join([f"Context: {c}" for c in context])

        system_prompt = """You are an expert at explaining social media posts with factual context.
Generate 3-5 concise bullet points explaining the post. 
Each bullet should cite its source using [Source N] notation.
Be clear, accurate, and cite your sources."""

        if image_analysis:
            user_prompt = f"""Post: {post}

Image Analysis: {image_analysis}

Background Context:
{context_str}

Please explain this post considering both the text and image."""
        else:
            user_prompt = f"""Post: {post}

Background Context:
{context_str}

Please explain this post."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.chat_endpoint,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                )

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return "Unable to generate explanation at this time.", {}

            data = response.json()
            explanation = data["choices"][0]["message"]["content"]
            token_usage = data.get("usage", {})

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_llm_call(
                provider="openai",
                model=self.model,
                prompt=user_prompt[:200],
                response=explanation[:200],
                tokens_used=token_usage,
                latency_ms=latency_ms,
            )

            return explanation, token_usage

        except Exception as e:
            logger.error(f"Failed to generate explanation: {str(e)}")
            return (
                "Unable to generate explanation due to a technical error.",
                {},
            )

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.embedding_endpoint,
                    headers=self.headers,
                    json={
                        "input": texts,
                        "model": self.embedding_model,
                    },
                )

            if response.status_code != 200:
                logger.error(f"Embeddings API error: {response.status_code} - {response.text}")
                return []

            data = response.json()
            embeddings = [item["embedding"] for item in data.get("data", [])]

            latency_ms = (time.time() - start_time) * 1000
            logger.debug(f"Generated {len(embeddings)} embeddings in {latency_ms:.2f}ms")

            return embeddings

        except Exception as e:
            logger.error(f"Failed to get embeddings: {str(e)}")
            return []

    async def analyze_image(self, image_url: str, post: str) -> Optional[str]:
        """Analyze an image using GPT-4o vision.

        Args:
            image_url: URL of the image
            post: The associated social media post

        Returns:
            Image analysis or None if failed
        """
        if not settings.ENABLE_IMAGE_UNDERSTANDING:
            return None

        start_time = time.time()

        system_prompt = "You are an expert at analyzing images and their context with social media posts. Provide a brief, factual analysis."

        user_prompt = f"""Analyze this image in the context of this social media post:

Post: {post}

Please provide a brief analysis of what's in the image and its relationship to the post."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.chat_endpoint,
                    headers=self.headers,
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": image_url},
                                    },
                                ],
                            },
                        ],
                        "max_tokens": 300,
                    },
                )

            if response.status_code != 200:
                logger.warning(f"Image analysis failed: {response.status_code}")
                return None

            data = response.json()
            analysis = data["choices"][0]["message"]["content"]

            latency_ms = (time.time() - start_time) * 1000
            logger.debug(f"Image analysis completed in {latency_ms:.2f}ms")

            return analysis

        except Exception as e:
            logger.warning(f"Image analysis error: {str(e)}")
            return None


# Global provider instance
openai_provider = OpenAIProvider()
