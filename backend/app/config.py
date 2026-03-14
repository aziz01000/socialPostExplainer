"""Configuration management."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # API
    debug: bool = False
    api_title: str = "Contextual Post Explainer"
    api_version: str = "1.0.0"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Google Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    
    # LLM
    llm_provider: str = "openai"
    
    # Retrieval
    top_k_documents: int = 5
    rerank_top_k: int = 3
    
    # Guardrails
    enable_input_moderation: bool = True
    enable_output_moderation: bool = True
    
    # Observability
    phoenix_enabled: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Print configuration at startup
print("\n" + "="*60)
print("Configuration Loaded:")
print("="*60)
print(f"LLM Provider: {settings.llm_provider}")
print(f"OpenAI Key: {'✓ Set' if settings.openai_api_key else '✗ Not set'}")
print(f"Gemini Key: {'✓ Set' if settings.gemini_api_key else '✗ Not set'}")
print(f"Input Moderation: {settings.enable_input_moderation}")
print(f"Output Moderation: {settings.enable_output_moderation}")
print("="*60 + "\n")

# Validate configuration
if settings.llm_provider == "openai" and not settings.openai_api_key:
    print(f"⚠️  WARNING: OpenAI provider selected but OPENAI_API_KEY not set")
elif settings.llm_provider == "gemini" and not settings.gemini_api_key:
    print(f"⚠️  WARNING: Gemini provider selected but GEMINI_API_KEY not set")
elif settings.llm_provider not in ["openai", "gemini"]:
    print(f"⚠️  WARNING: Unknown LLM provider: {settings.llm_provider}")
