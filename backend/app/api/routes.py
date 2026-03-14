"""FastAPI routes for the Post Explainer service."""

import logging

from fastapi import APIRouter, HTTPException
from app.agents import post_explainer_agent
from app.models import ExplainRequest, ExplainResponse, Source

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
async def explain_post(request: ExplainRequest) -> ExplainResponse:
    """Explain a social media post.

    Args:
        request: ExplainRequest containing post and optional image_url

    Returns:
        ExplainResponse with explanation and sources

    Raises:
        HTTPException: If explanation generation fails
    """
    try:
        logger.info(f"Processing post: {request.post[:50]}...")

        # Run agent
        state = await post_explainer_agent.run(
            post=request.post,
            image_url=request.image_url,
        )

        # Check for errors
        if state.error:
            logger.error(f"Agent error: {state.error}")
            raise HTTPException(status_code=400, detail=state.error)

        if not state.moderation_input_safe:
            raise HTTPException(
                status_code=400,
                detail="Input content violates content policy",
            )

        # Build response
        response = ExplainResponse(
            explanation=state.explanation,
            sources=state.sources,
            image_analysis=state.image_analysis,
        )

        logger.info("Post explained successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process request",
        )


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}
