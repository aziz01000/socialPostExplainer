"""FastAPI application entry point."""

import asyncio
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.api.routes import router
from app.agents.post_explainer_agent import PostExplainerAgent

# Global agent instance
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    global agent
    
    # Startup
    agent = PostExplainerAgent()
    await agent.initialize()
    print("✓ Agent initialized")
    
    yield
    
    # Shutdown
    print("✓ Agent cleanup")


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

# Include routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
