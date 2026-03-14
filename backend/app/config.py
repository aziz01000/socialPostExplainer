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
