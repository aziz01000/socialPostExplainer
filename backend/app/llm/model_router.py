"""LLM model routing. All LLM calls are traced to Arize Phoenix when enabled."""

from app.config import settings
from app.llm.openai_provider import OpenAIProvider


def _llm_model_name() -> str:
    if settings.llm_provider.lower() == "openai":
        return getattr(settings, "openai_model", "openai")
    return getattr(settings, "gemini_model", "gemini")


def _embedding_model_name() -> str:
    return getattr(settings, "embedding_model", "embedding")


class ModelRouter:
    """Route LLM calls to appropriate provider."""
    
    def __init__(self):
        provider = settings.llm_provider.lower().strip()
        embedding_provider = settings.embedding_provider.lower().strip()
        
        if provider == "openai":
            self.provider = OpenAIProvider()
            print(f"✓ ModelRouter initialized with OpenAI provider")
        elif provider == "gemini":
            from app.llm.gemini_provider import GeminiProvider
            self.provider = GeminiProvider()
            print(f"✓ ModelRouter initialized with Gemini provider")
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
        
        # Initialize embedding provider (can be different from LLM provider)
        if embedding_provider == "openai":
            self.embedding_provider = OpenAIProvider()
            print(f"✓ Embedding provider: OpenAI ({settings.embedding_model}, {settings.embedding_dimensions}d)")
        elif embedding_provider == "gemini":
            from app.llm.gemini_provider import GeminiProvider
            self.embedding_provider = GeminiProvider()
            print(f"✓ Embedding provider: Gemini ({settings.embedding_model}, {settings.embedding_dimensions}d)")
        else:
            # Default to same provider as LLM
            self.embedding_provider = self.provider
            print(f"✓ Embedding provider: Same as LLM provider")
        
        self._langchain_llm = None
    
    def get_llm_instance(self):
        """Get LangChain-compatible LLM instance."""
        if self._langchain_llm is not None:
            return self._langchain_llm
        
        # Create LangChain LLM wrapper based on provider
        if isinstance(self.provider, OpenAIProvider):
            from langchain_openai import ChatOpenAI
            self._langchain_llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.7
            )
        else:  # Gemini
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._langchain_llm = ChatGoogleGenerativeAI(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                temperature=0.7
            )
        
        return self._langchain_llm
    
    async def generate_embeddings(self, texts: list) -> list:
        """Generate embeddings using embedding provider (traced to Phoenix)."""
        from app.observability.phoenix_tracing import trace_embedding

        model = getattr(settings, "embedding_model", None) or "embedding"
        async with trace_embedding("embedding.generate", _embedding_model_name(), texts) as (_span, set_output):
            if model:
                result = await self.embedding_provider.generate_embeddings(texts, model=model)
            else:
                result = await self.embedding_provider.generate_embeddings(texts)
            set_output(result)
        return result

    async def generate_completion(self, messages: list) -> str:
        """Generate completion using LLM provider (traced to Phoenix)."""
        from app.observability.phoenix_tracing import trace_llm

        async with trace_llm(
            "llm.chat_completion",
            _llm_model_name(),
            messages,
            invocation_parameters={"temperature": 0.7, "max_tokens": 2048},
        ) as (_span, set_output):
            result, usage = await self.provider.generate_chat_completion(messages)
            set_output(result, token_usage=usage)
        return result

    async def check_moderation(self, text: str) -> dict:
        """Check moderation using LLM provider (traced to Phoenix as guardrail)."""
        from app.observability.phoenix_tracing import trace_guardrail

        async with trace_guardrail("guardrail.moderation", (text or "")[:500]) as (_span, set_output):
            result = await self.provider.check_moderation(text)
            set_output(result)
        return result

    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using LLM provider (traced to Phoenix)."""
        from app.observability.phoenix_tracing import trace_llm

        input_messages = [{"role": "user", "content": [{"type": "text", "text": question}, {"type": "image_url", "image_url": {"url": image_url}}]}]
        async with trace_llm("llm.vision.analyze_image", _llm_model_name(), input_messages) as (_span, set_output):
            result, usage = await self.provider.analyze_image(image_url, question)
            set_output(result, token_usage=usage)
        return result
