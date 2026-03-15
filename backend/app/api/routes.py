"""API routes."""

import base64
import time
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from app.models.schemas import (
    AskRequest,
    AskResponse,
    ExplainRequest,
    ExplainResponse,
    QARequest,
    QAResponse,
    HealthResponse,
    _context_sources_from_sources,
)
from app.config import settings
from app.observability.phoenix_tracing import trace_request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.api_version
    )


def _to_data_url(image_base64: Optional[str]) -> Optional[str]:
    """Convert raw base64 image bytes to data URL."""
    if not image_base64:
        return None
    raw = image_base64.strip()
    if not raw:
        return None
    if raw.startswith("data:image/"):
        return raw
    return f"data:image/png;base64,{raw}"


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, req: Request):
    """
    Unified endpoint with all explain features:
    - question (required)
    - image_url or image upload (via image_base64 / /ask/upload)
    - sources_type filter: all/social/news
    """
    agent = req.app.state.agent
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    if request.sources_type not in ["all", "social", "news"]:
        raise HTTPException(status_code=400, detail="sources_type must be 'all', 'social', or 'news'")

    try:
        start_time = time.time()
        image_input = _to_data_url(request.image_base64) or request.image_url

        async with trace_request("ask", (request.question or "")[:300]):
            result = await agent.explain_post(
                post_content=request.question,
                image_url=image_input,
                sources_type=request.sources_type,
            )

        processing_time = (time.time() - start_time) * 1000
        sources_out = result["sources"][: request.context_limit]
        context_sources_used, context_note = _context_sources_from_sources(sources_out)

        return AskResponse(
            explanation=result["explanation"],
            sources=sources_out,
            image_analysis=result.get("image_analysis"),
            processing_time_ms=processing_time,
            tool_trace=result.get("tool_trace") if request.debug else None,
            context_sources_used=context_sources_used,
            context_note=context_note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ask error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask/upload", response_model=AskResponse)
async def ask_upload(
    req: Request,
    question: str = Form(...),
    sources_type: str = Form("all"),
    context_limit: int = Form(5),
    debug: bool = Form(False),
    image_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """Same as /ask, but accepts multipart file upload."""
    image_base64 = None
    if image and image.filename:
        try:
            content = await image.read()
            if content:
                image_base64 = base64.b64encode(content).decode("ascii")
        except Exception as e:
            logger.warning(f"Failed reading uploaded image: {e}")

    body = AskRequest(
        question=question,
        image_url=image_url,
        image_base64=image_base64,
        sources_type=sources_type,
        context_limit=context_limit,
        debug=debug,
    )
    return await ask(body, req)


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
        input_preview = (request.post_content or "")[:300]
        async with trace_request("explain_post", input_preview):
            result = await agent.explain_post(
                post_content=request.post_content,
                image_url=request.image_url,
                sources_type="all",
            )
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        sources_out = result["sources"][:request.context_limit]
        context_sources_used, context_note = _context_sources_from_sources(sources_out)

        return ExplainResponse(
            explanation=result["explanation"],
            sources=sources_out,
            image_analysis=result.get("image_analysis"),
            processing_time_ms=processing_time,
            tool_trace=result.get("tool_trace") if request.debug else None,
            context_sources_used=context_sources_used,
            context_note=context_note,
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
        if request.sources_type not in ["all", "social", "news"]:
            raise ValueError("sources_type must be 'all', 'social', or 'news'")

        input_preview = (request.question or "")[:300]
        async with trace_request("social_qa", input_preview):
            result = await qa_agent.answer_question(request.question, request.sources_type)

        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"QA processing completed in {processing_time:.0f}ms")
        
        return QAResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result["sources"],
            source_breakdown=result["source_breakdown"],
            processing_time_ms=processing_time,
            tool_trace=result.get("tool_trace") if request.debug else None,
        )
    except ValueError as e:
        # Moderation or validation error
        error_msg = str(e)
        logger.warning(f"Input validation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"QA processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
