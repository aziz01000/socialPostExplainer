"""Configuration management with comprehensive logging."""

import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        case_sensitive=False
    )
    
    # API
    debug: bool = False
    api_title: str = "Contextual Post Explainer"
    api_version: str = "1.0.0"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Google Gemini Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3-flash-preview"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    
    # Social Media API Keys (Optional)
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    
    # News API Keys (Optional)
    newsdata_api_key: Optional[str] = None
    newsapi_api_key: Optional[str] = None
    guardian_api_key: Optional[str] = None
    
    # LLM Provider Selection
    # Default to OpenAI for this take-home since an OpenAI key is provided.
    llm_provider: str = "openai"
    
    # Embedding Configuration (separate from LLM provider for flexibility)
    # The repo ships a FAISS index built with 1536-d OpenAI embeddings.
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Retrieval
    top_k_documents: int = 5
    rerank_top_k: int = 3
    
    # Guardrails
    enable_input_moderation: bool = True
    enable_output_moderation: bool = True
    
    # Observability (Arize Phoenix)
    phoenix_enabled: bool = True
    phoenix_project_name: str = "contextual-post-explainer"
    phoenix_collector_endpoint: Optional[str] = None  # e.g. http://localhost:6006 or Phoenix Cloud URL
    log_level: str = "INFO"


settings = Settings()

# Configure logging level from settings
logging.getLogger().setLevel(settings.log_level)

# Print configuration at startup
print("\n" + "="*70)
print("Configuration Loaded:")
print("="*70)
print(f"LLM Provider: {settings.llm_provider.upper()}")
print(f"\nOpenAI:")
print(f"  API Key: {'✓ Set' if settings.openai_api_key else '✗ Not set'}")
print(f"  Model: {settings.openai_model}")
print(f"  Base URL: {settings.openai_base_url}")
print(f"\nGemini:")
print(f"  API Key: {'✓ Set' if settings.gemini_api_key else '✗ Not set'}")
print(f"  Model: {settings.gemini_model}")
print(f"  Base URL: {settings.gemini_base_url}")
print(f"\nEmbedding Provider: {settings.embedding_provider.upper()}")
print(f"  Model: {settings.embedding_model}")
print(f"  Dimensions: {settings.embedding_dimensions}")
print(f"\nSocial Media APIs (for Q&A):")
print(f"  Reddit: {'✓ Configured' if settings.reddit_client_id else '✗ Not configured (will use mock data)'}")
print(f"  Twitter: {'✓ Configured' if settings.twitter_bearer_token else '✗ Not configured (will use mock data)'}")
print(f"\nNews APIs (for Q&A):")
print(f"  NewsData.io: {'✓ Configured' if settings.newsdata_api_key else '✗ Not configured (will use mock data)'}")
print(f"  NewsAPI: {'✓ Configured' if settings.newsapi_api_key else '✗ Not configured (will use mock data)'}")
print(f"  The Guardian: {'✓ Configured' if settings.guardian_api_key else '✗ Not configured (will use mock data)'}")
print(f"\nGuardrails:")
print(f"  Input Moderation: {settings.enable_input_moderation}")
print(f"  Output Moderation: {settings.enable_output_moderation}")
print(f"\nLogging Level: {settings.log_level}")
print("="*70 + "\n")

# Validate configuration
logger.info(f"Loading configuration for provider: {settings.llm_provider.upper()}")

if settings.llm_provider.lower() == "openai":
    if not settings.openai_api_key:
        logger.error("⚠️  ERROR: OpenAI provider selected but OPENAI_API_KEY not set")
    else:
        logger.info("✓ OpenAI provider configured successfully")
elif settings.llm_provider.lower() == "gemini":
    if not settings.gemini_api_key:
        logger.error("⚠️  ERROR: Gemini provider selected but GEMINI_API_KEY not set")
    else:
        logger.info("✓ Gemini provider configured successfully")
else:
    logger.error(f"⚠️  ERROR: Unknown LLM provider: {settings.llm_provider}")

logger.info(f"Embedding provider: {settings.embedding_provider.upper()} ({settings.embedding_model}, {settings.embedding_dimensions}-dim)")
