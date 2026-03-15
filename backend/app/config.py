"""Configuration management with comprehensive logging."""

import logging
from pydantic import Field
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
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # API
    debug: bool = Field(default=False, validation_alias="DEBUG")
    api_title: str = Field(default="Contextual Post Explainer", validation_alias="API_TITLE")
    api_version: str = Field(default="1.0.0", validation_alias="API_VERSION")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_BASE_URL")
    
    # Google Gemini Configuration
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3-flash-preview", validation_alias="GEMINI_MODEL")
    gemini_base_url: str = Field(default="https://generativelanguage.googleapis.com", validation_alias="GEMINI_BASE_URL")
    
    # Social Media API Keys (Optional)
    reddit_client_id: Optional[str] = Field(default=None, validation_alias="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(default=None, validation_alias="REDDIT_CLIENT_SECRET")
    twitter_bearer_token: Optional[str] = Field(default=None, validation_alias="TWITTER_BEARER_TOKEN")
    
    # News API Keys (Optional)
    newsdata_api_key: Optional[str] = Field(default=None, validation_alias="NEWSDATA_API_KEY")
    newsapi_api_key: Optional[str] = Field(default=None, validation_alias="NEWSAPI_API_KEY")
    guardian_api_key: Optional[str] = Field(default=None, validation_alias="GUARDIAN_API_KEY")
    
    # LLM Provider Selection
    # Default to OpenAI for this take-home since an OpenAI key is provided.
    llm_provider: str = Field(default="openai", validation_alias="LLM_PROVIDER")
    
    # Embedding Configuration (separate from LLM provider for flexibility)
    # The repo ships a FAISS index built with 1536-d OpenAI embeddings.
    embedding_provider: str = Field(default="openai", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, validation_alias="EMBEDDING_DIMENSIONS")
    
    # Retrieval
    top_k_documents: int = Field(default=5, validation_alias="TOP_K_DOCUMENTS")
    rerank_top_k: int = Field(default=3, validation_alias="RERANK_TOP_K")
    # Vector DB: fetch more candidates then keep only relevant ones (don't show vector_db if nothing is relevant)
    vector_db_initial_k: int = Field(default=20, validation_alias="VECTOR_DB_INITIAL_K")
    vector_db_relevance_threshold: float = Field(default=0.45, validation_alias="VECTOR_DB_RELEVANCE_THRESHOLD")
    
    # Guardrails
    enable_input_moderation: bool = Field(default=True, validation_alias="ENABLE_INPUT_MODERATION")
    enable_output_moderation: bool = Field(default=True, validation_alias="ENABLE_OUTPUT_MODERATION")
    
    # Observability (Arize Phoenix)
    phoenix_enabled: bool = Field(default=True, validation_alias="PHOENIX_ENABLED")
    phoenix_project_name: str = Field(default="contextual-post-explainer", validation_alias="PHOENIX_PROJECT_NAME")
    phoenix_collector_endpoint: Optional[str] = Field(default=None, validation_alias="PHOENIX_COLLECTOR_ENDPOINT")  # e.g. http://localhost:6006 or Phoenix Cloud URL
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


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
