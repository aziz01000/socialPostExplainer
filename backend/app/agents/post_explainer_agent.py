"""Core agent for explaining social media posts.

Design:
- LangGraph workflow: moderation → (optional image) → retrieve → generate → post_process → output moderation.
- Retrieve context from FAISS + external sources + web (Wikipedia); rerank with embeddings.
- Generate 3-5 bullet explanations with inline citations [S1], [S2].
"""

import logging
from typing import Dict, List, Optional, Any

from app.graphs.explain_graph import create_explain_graph
from app.llm.model_router import ModelRouter
from app.retrieval.vector_store import VectorStore
from app.retrieval.web_search import WebSearch
from app.retrieval.social_media_search import ExternalSourcesSearch
from app.guardrails.moderation import ModerationGuardrail

logger = logging.getLogger(__name__)


class PostExplainerAgent:
    """Agent for explaining posts with context and citations (LangGraph)."""

    def __init__(self):
        logger.info("Initializing PostExplainerAgent")
        self.model_router = ModelRouter()
        self.vector_store = VectorStore()
        self.web_search = WebSearch()
        self.external_sources = ExternalSourcesSearch()
        self.moderation = ModerationGuardrail()
        self._graph = create_explain_graph()

    async def initialize(self):
        """Initialize agent components."""
        logger.info("Initializing vector store...")
        await self.vector_store.initialize()
        logger.info("✓ PostExplainerAgent fully initialized")

    async def explain_post(
        self,
        post_content: str,
        image_url: Optional[str] = None,
        sources_type: str = "all",
    ) -> Dict[str, Any]:
        """
        Explain a social media post via LangGraph workflow.

        Returns:
        - explanation: 3-5 bullets with citations like [S1]
        - sources: list of structured sources
        - image_analysis: optional vision result
        """
        logger.info(f"Starting explain_post workflow for post ({len(post_content)} chars)")

        initial_state = {
            "post_content": post_content,
            "image_url": image_url,
            "sources_type": sources_type,
            "agent": self,
            "tool_trace": [],
        }
        final_state = await self._graph.ainvoke(initial_state)

        if final_state.get("moderation_flagged"):
            mod = final_state.get("moderation_result") or {}
            error_msg = (
                f"❌ Input not compliant ({mod.get('category')}): "
                f"{mod.get('reason', 'Content violates policy')}. Please change your query and try again."
            )
            logger.warning(f"✗ Input blocked - {error_msg}")
            raise ValueError(error_msg)

        if final_state.get("output_moderation_flagged"):
            error_msg = (
                "❌ Generated content not compliant. Content violates policy. Please change your query and try again."
            )
            logger.warning("✗ Output blocked - generated content not compliant")
            raise ValueError(error_msg)

        return {
            "explanation": final_state.get("explanation_bullets") or [],
            "sources": final_state.get("sources") or [],
            "image_analysis": final_state.get("image_analysis"),
            "tool_trace": final_state.get("tool_trace") or [],
        }