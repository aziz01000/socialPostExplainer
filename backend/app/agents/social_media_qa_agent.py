"""Agent for answering questions using FAISS + external sources (LangGraph)."""

import logging
from typing import Dict, List, Optional, Any

from app.graphs.qa_graph import create_qa_graph
from app.llm.model_router import ModelRouter
from app.retrieval.vector_store import VectorStore
from app.retrieval.social_media_search import ExternalSourcesSearch
from app.retrieval.web_search import WebSearch
from app.guardrails.moderation import ModerationGuardrail

logger = logging.getLogger(__name__)


class SocialMediaQAAgent:
    """Question-answering agent combining FAISS + external sources (LangGraph)."""

    def __init__(self):
        logger.info("Initializing SocialMediaQAAgent")
        self.model_router = ModelRouter()
        self.vector_store = VectorStore()
        self.external_sources = ExternalSourcesSearch()
        self.web_search = WebSearch()
        self.moderation = ModerationGuardrail()
        self._graph = create_qa_graph()

    async def initialize(self):
        """Initialize agent components."""
        logger.info("Initializing vector store for QA agent...")
        await self.vector_store.initialize()
        logger.info("✓ SocialMediaQAAgent fully initialized")

    async def answer_question(self, question: str, sources_type: str = "all") -> Dict[str, Any]:
        """Answer a question via LangGraph workflow."""
        logger.info(f"Processing question: '{question}' (source_type={sources_type})")

        if sources_type not in ["all", "social", "news"]:
            raise ValueError("sources_type must be 'all', 'social', or 'news'")

        initial_state = {
            "question": question,
            "sources_type": sources_type,
            "agent": self,
            "tool_trace": [],
        }
        final_state = await self._graph.ainvoke(initial_state)

        if final_state.get("moderation_flagged"):
            mod = final_state.get("moderation_result") or {}
            error_msg = (
                f"❌ Question not compliant ({mod.get('category')}): "
                f"{mod.get('reason', 'Content violates policy')}. Please change your query and try again."
            )
            logger.warning(f"✗ Question blocked - {error_msg}")
            raise ValueError(error_msg)

        if final_state.get("output_moderation_flagged"):
            error_msg = (
                "❌ Generated answer not compliant. Content violates policy. Please change your query and try again."
            )
            logger.warning("✗ Answer blocked - generated content not compliant")
            raise ValueError(error_msg)

        sources = final_state.get("sources") or []
        return {
            "question": question,
            "answer": {
                "summary": final_state.get("answer_text") or "",
                "source_count": len(sources),
                "generated": True,
            },
            "sources": sources,
            "source_breakdown": {
                "combined_total": len(sources),
                "platforms": final_state.get("platforms") or {},
            },
            "tool_trace": final_state.get("tool_trace") or [],
        }

    async def close(self):
        """Cleanup resources."""
        logger.info("Closing SocialMediaQAAgent")
        await self.external_sources.close()