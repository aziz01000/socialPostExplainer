"""Data models and schemas for the API."""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Citation source."""
    title: str
    context: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    url: Optional[str] = None
    platform: Optional[str] = None  # e.g., "vector_db", "reddit", "wikipedia"
    engagement_score: Optional[int] = None  # e.g., likes, comments
    author: Optional[str] = None


class ExplainRequest(BaseModel):
    """API request to explain a post."""
    post_content: str = Field(..., min_length=1, max_length=5000)
    image_url: Optional[str] = None
    context_limit: int = Field(default=5, ge=1, le=20)
    debug: bool = Field(default=False, description="Include tool traces in the response")


class ContextSourcesUsed(BaseModel):
    """Which retrieval sources contributed to the response."""
    vector_db: bool = False  # FAISS / local document index
    web: bool = False       # Wikipedia or other web
    web_available: bool = False  # True if web returned real results (not placeholder)
    external: bool = False  # Social / news APIs


def _context_sources_from_sources(sources: List[Source]) -> Tuple[ContextSourcesUsed, str]:
    """Derive context_sources_used and a short context_note from the sources list."""
    used = ContextSourcesUsed()
    for s in sources or []:
        p = (s.platform or "").lower()
        if p == "vector_db":
            used.vector_db = True
        elif p in ("web", "wikipedia"):
            used.web = True
            if s.url and "unavailable" not in (s.context or "").lower() and "unavailable" not in (s.title or "").lower():
                used.web_available = True
        elif p in ("reddit", "twitter", "news", "external", "guardian", "newsapi", "newsdata"):
            used.external = True
    if not used.web_available and used.web:
        used.web_available = False
    parts = []
    if used.vector_db:
        parts.append("local document index (vector DB)")
    if used.web_available:
        parts.append("web (Wikipedia)")
    elif used.web:
        parts.append("web (unavailable)")
    if used.external:
        parts.append("social/news APIs")
    note = "Context from " + ", ".join(parts) + "." if parts else "No external context used."
    return used, note


class ExplainResponse(BaseModel):
    """API response with explanation and sources."""
    explanation: List[str]
    sources: List[Source]
    image_analysis: Optional[str] = None
    processing_time_ms: float
    tool_trace: Optional[List[Dict[str, Any]]] = None
    context_sources_used: Optional[ContextSourcesUsed] = None
    context_note: Optional[str] = None


class QARequest(BaseModel):
    """API request for Q&A with external sources search."""
    question: str = Field(..., min_length=3, max_length=1000)
    sources_type: str = Field(default="all", description="Source type: 'all', 'social', or 'news'")
    debug: bool = Field(default=False, description="Include tool traces in the response")


class QAResponse(BaseModel):
    """API response with answer and combined sources."""
    question: str
    answer: dict = Field(description="Generated answer with summary and metadata")
    sources: List[Source]
    source_breakdown: dict = Field(description="Breakdown of sources by type and platform")
    processing_time_ms: float
    tool_trace: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
