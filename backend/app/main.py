"""Main FastAPI application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="AI-powered social media post explainer with RAG and observability",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    @app.on_event("startup")
    async def startup():
        """Startup event handler."""
        logger.info(f"Starting {settings.API_TITLE}")
        logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
        logger.info(f"Phoenix Tracing: {settings.PHOENIX_ENABLED}")

    @app.on_event("shutdown")
    async def shutdown():
        """Shutdown event handler."""
        logger.info(f"Shutting down {settings.API_TITLE}")
        # Export traces
        if settings.PHOENIX_ENABLED:
            from app.observability import tracer
            tracer.export_traces("./traces.json")
            logger.info("Traces exported to traces.json")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
