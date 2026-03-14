"""FastAPI application entry point."""

import asyncio
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# Configure root logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    
    # Startup
    try:
        logger.info("Starting application...")
        from app.agents.post_explainer_agent import PostExplainerAgent
        
        agent = PostExplainerAgent()
        await agent.initialize()
        app.state.agent = agent
        logger.info("✓ Agent initialized and ready")
    except Exception as e:
        logger.error(f"✗ Agent initialization failed: {e}", exc_info=True)
        app.state.agent = None
        raise
    
    yield
    
    # Shutdown
    logger.info("✓ Agent cleanup completed")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes after app is created to avoid circular imports
from app.api.routes import router
app.include_router(router)

logger.info("✓ FastAPI application created and routes registered")


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.log_level.lower())
