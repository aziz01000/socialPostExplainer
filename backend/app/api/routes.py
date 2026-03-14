"""API routes."""

import time
import logging
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import ExplainRequest, ExplainResponse, QARequest, QAResponse, HealthResponse
from app.config import settings

logger = logging.getLogger(__name__)
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
        # Moderation or validation error
        error_msg = str(e)
        logger.warning(f"Input validation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Explain post error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social-qa", response_model=QAResponse)
async def social_media_qa(request: QARequest, req: Request):
    """
    Answer questions using FAISS + external sources (social media & news APIs).
    
    Combines:
    - Authoritative documents from FAISS vector store
    - Social media discussions (Reddit, Twitter)
    - News articles (NewsData.io, NewsAPI, The Guardian)
    - LLM synthesis of diverse perspectives
    
    - **question**: The question to answer (3-1000 chars)
    - **sources_type**: 'all' (default), 'social' (Reddit, Twitter only), or 'news' (News APIs only)
    """
    # Get QA agent from app state
    qa_agent = req.app.state.qa_agent
    
    if not qa_agent:
        logger.error("QA agent not initialized")
        raise HTTPException(status_code=500, detail="QA agent not initialized")
    
    try:
        logger.info(f"Processing QA request: {request.question} (sources_type={request.sources_type})")
        start_time = time.time()
        
        # Validate sources_type
        if request.sources_type not in ["all", "social", "news"]:
            raise ValueError("sources_type must be 'all', 'social', or 'news'")
        
        # Run QA agent
        result = await qa_agent.answer_question(request.question, request.sources_type)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"QA processing completed in {processing_time:.0f}ms")
        
        return QAResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result["sources"],
            source_breakdown=result["source_breakdown"],
            processing_time_ms=processing_time
        )
    except ValueError as e:
        # Moderation or validation error
        error_msg = str(e)
        logger.warning(f"Input validation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"QA processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
