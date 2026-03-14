"""API routes."""

import time
from fastapi import APIRouter, HTTPException, Request
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
async def explain_post(request: ExplainRequest, req: Request):
    """
    Explain a social media post with retrieval and LLM generation.
    
    - **post_content**: The post text to explain
    - **image_url**: Optional image URL for vision analysis
    - **context_limit**: Max number of context sources (1-20)
    """
    # Get agent from app state
    agent = req.app.state.agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        start_time = time.time()
        
        # Run agent
        result = await agent.explain_post(
            post_content=request.post_content,
            image_url=request.image_url
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return ExplainResponse(
            explanation=result["explanation"],
            sources=result["sources"][:request.context_limit],
            image_analysis=result.get("image_analysis"),
            processing_time_ms=processing_time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
