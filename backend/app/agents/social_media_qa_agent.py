"""Agent for answering questions using FAISS + external sources."""

import logging
from typing import Dict, List, Optional, Any
from app.models.schemas import Source
from app.llm.model_router import ModelRouter
from app.retrieval.vector_store import VectorStore
from app.retrieval.social_media_search import ExternalSourcesSearch
from app.retrieval.web_search import WebSearch
from app.guardrails.moderation import ModerationGuardrail
from app.config import settings
from app.agents.tools import build_sources_for_post, format_sources_for_prompt

logger = logging.getLogger(__name__)


class SocialMediaQAAgent:
    """Question-answering agent combining FAISS + external sources."""
    
    def __init__(self):
        logger.info("Initializing SocialMediaQAAgent")
        self.model_router = ModelRouter()
        self.vector_store = VectorStore()
        self.external_sources = ExternalSourcesSearch()
        self.web_search = WebSearch()
        self.moderation = ModerationGuardrail()
    
    async def initialize(self):
        """Initialize agent components."""
        logger.info("Initializing vector store for QA agent...")
        await self.vector_store.initialize()
        logger.info("✓ SocialMediaQAAgent fully initialized")
    
    async def answer_question(self, question: str, sources_type: str = "all") -> Dict[str, Any]:
        """
        Answer a question by synthesizing FAISS + external sources + web context.
        """
        logger.info(f"Processing question: '{question}' (source_type={sources_type})")
        
        # Step 1: Input guardrail - Block non-compliant questions
        moderation_result = await self._input_guardrail(question)
        if moderation_result.get("flagged"):
            error_msg = f"❌ Question not compliant ({moderation_result.get('category')}): {moderation_result.get('reason', 'Content violates policy')}. Please change your query and try again."
            logger.warning(f"✗ Step 1: Question blocked - {error_msg}")
            raise ValueError(error_msg)
        
        # Validate sources_type
        if sources_type not in ["all", "social", "news"]:
            raise ValueError("sources_type must be 'all', 'social', or 'news'")
        
        try:
            # Reuse the same retrieval stack as post explainer, but treat the "question" as the query.
            sources = await build_sources_for_post(
                post_content=question,
                vector_store=self.vector_store,
                web_search=self.web_search,
                external_sources=self.external_sources,
                model_router=self.model_router,
                top_k=12,
                sources_type=sources_type,
            )

            sources_block = format_sources_for_prompt(sources)

            system = (
                "You answer questions by synthesizing the provided sources. "
                "Be explicit about uncertainty. "
                "Cite claims with [S1] style citations."
            )
            user = (
                f"Question:\n{question}\n\n"
                f"Sources:\n{sources_block}\n\n"
                "Write a concise answer with:\n"
                "1. A short direct answer\n"
                "2. 3-6 bullet key points, each with citations\n"
            )

            answer_text = await self.model_router.generate_completion(
                [{"role": "system", "content": system}, {"role": "user", "content": user}]
            )

            output_check = await self._output_guardrail(answer_text)
            if output_check.get("flagged"):
                error_msg = f"❌ Generated answer not compliant ({output_check.get('category')}): {output_check.get('reason', 'Content violates policy')}. Please change your query and try again."
                logger.warning(f"✗ Answer blocked - {error_msg}")
                raise ValueError(error_msg)

            # Basic breakdown for UI/debugging.
            platforms = {}
            for s in sources:
                p = (s.platform or "unknown").lower()
                platforms[p] = platforms.get(p, 0) + 1

            return {
                "question": question,
                "answer": {
                    "summary": answer_text,
                    "source_count": len(sources),
                    "generated": True
                },
                "sources": sources,
                "source_breakdown": {
                    "combined_total": len(sources),
                    "platforms": platforms,
                }
            }
            
        except Exception as e:
            logger.error(f"✗ Agent workflow error: {e}", exc_info=True)
            raise
    
    async def _input_guardrail(self, text: str) -> dict:
        """Step 1: Check input question for policy violations."""
        result = await self.moderation.check_input(text)
        return result
    
    async def _output_guardrail(self, text: str) -> dict:
        """Step 6: Check generated answer for policy violations."""
        result = await self.moderation.check_output(text)
        return result
    
    async def close(self):
        """Cleanup resources."""
        logger.info("Closing SocialMediaQAAgent")
        await self.external_sources.close()
