"""API routes."""

from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ExplainRequest, ExplainResponse, HealthResponse
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.api_version
    )


@router.post("/explain", response_model=ExplainResponse)
async def explain_post(request: ExplainRequest):
    """
    Explain a social media post with retrieval and LLM generation.
    
    - **post_content**: The post text to explain
    - **image_url**: Optional image URL for vision analysis
    - **context_limit**: Max number of context sources (1-20)
    """
    try:
        # Placeholder - to be implemented with agent
        return ExplainResponse(
            explanation=["Explanation coming soon"],
            sources=[],
            processing_time_ms=0.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
