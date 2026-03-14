"""Configuration module for the Contextual Post Explainer application."""

import os
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_TITLE: str = "Contextual Post Explainer"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # LLM Router Configuration
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"

    # Vector Store Configuration
    FAISS_INDEX_PATH: str = "./data/faiss_index.pkl"
    EMBEDDINGS_CACHE_PATH: str = "./data/embeddings_cache.json"

    # Phoenix Configuration
    PHOENIX_ENABLED: bool = True
    PHOENIX_PROJECT_NAME: str = "contextual-post-explainer"
    PHOENIX_ENDPOINT: str = "http://localhost:6006"

    # Retrieval Configuration
    TOP_K_DOCUMENTS: int = 5
    RERANK_TOP_K: int = 3

    # Guardrails Configuration
    ENABLE_INPUT_MODERATION: bool = True
    ENABLE_OUTPUT_MODERATION: bool = True

    # Image Understanding
    ENABLE_IMAGE_UNDERSTANDING: bool = True
    MAX_IMAGE_SIZE_MB: int = 10

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


settings = get_settings()
