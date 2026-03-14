"""Pydantic schemas for request/response models."""

from typing import Optional

from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    """Request model for the /explain endpoint."""

    post: str = Field(..., description="The social media post to explain", min_length=1)
    image_url: Optional[str] = Field(
        None, description="Optional URL to an image associated with the post"
    )


class Source(BaseModel):
    """Individual source citation."""

    url: str = Field(..., description="URL of the source")
    title: Optional[str] = Field(None, description="Title of the source")
    context: Optional[str] = Field(None, description="Relevant context from the source")


class ExplainResponse(BaseModel):
    """Response model for the /explain endpoint."""

    explanation: str = Field(..., description="Bullet-point explanation of the post")
    sources: list[Source] = Field(..., description="List of source citations")
    image_analysis: Optional[str] = Field(
        None, description="Analysis of the image if image_url was provided"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class RetrievalResult(BaseModel):
    """Result from the retrieval layer."""

    document: str = Field(..., description="Retrieved document content")
    source: str = Field(..., description="Source of the document")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    url: Optional[str] = Field(None, description="URL of the source")


class AgentState(BaseModel):
    """State passed through the agent workflow."""

    post: str = Field(..., description="The original social media post")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    moderation_input_safe: bool = Field(True, description="Whether input passed moderation")
    retrieval_results: list[RetrievalResult] = Field(
        default_factory=list, description="Retrieved documents"
    )
    reranked_results: list[RetrievalResult] = Field(
        default_factory=list, description="Reranked documents"
    )
    image_analysis: Optional[str] = Field(None, description="Analysis of image if provided")
    explanation: str = Field(default="", description="Generated explanation")
    moderation_output_safe: bool = Field(True, description="Whether output passed moderation")
    sources: list[Source] = Field(default_factory=list, description="Source citations")
    error: Optional[str] = Field(None, description="Error message if any")
