"""LLM model routing."""

from app.config import settings
from app.llm.openai_provider import OpenAIProvider


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
        """Generate embeddings using embedding provider."""
        return await self.embedding_provider.generate_embeddings(texts)
    
    async def generate_completion(self, messages: list) -> str:
        """Generate completion using LLM provider."""
        return await self.provider.generate_chat_completion(messages)
    
    async def check_moderation(self, text: str) -> dict:
        """Check moderation using LLM provider."""
        return await self.provider.check_moderation(text)
    
    async def analyze_image(self, image_url: str, question: str) -> str:
        """Analyze image using LLM provider."""
        return await self.provider.analyze_image(image_url, question)
