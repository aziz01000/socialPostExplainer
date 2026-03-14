"""Data models and schemas for the API."""

from typing import Optional, List
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Citation source."""
    title: str
    context: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    url: Optional[str] = None


class ExplainRequest(BaseModel):
    """API request to explain a post."""
    post_content: str = Field(..., min_length=1, max_length=5000)
    image_url: Optional[str] = None
    context_limit: int = Field(default=5, ge=1, le=20)


class ExplainResponse(BaseModel):
    """API response with explanation and sources."""
    explanation: List[str]
    sources: List[Source]
    image_analysis: Optional[str] = None
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
