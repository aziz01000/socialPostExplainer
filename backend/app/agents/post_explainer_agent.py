"""Core agent for explaining social media posts.

Design:
- Retrieve context from a local FAISS vector store + external sources + web (Wikipedia).
- Rerank sources with embeddings when available.
- Generate 3-5 bullet explanations with inline citations like [S1], [S2].
"""

import logging
from typing import Dict, List, Optional, Any
from app.llm.model_router import ModelRouter
from app.retrieval.vector_store import VectorStore
from app.retrieval.web_search import WebSearch
from app.retrieval.social_media_search import ExternalSourcesSearch
from app.guardrails.moderation import ModerationGuardrail
from app.agents.tools import build_sources_for_post, format_sources_for_prompt

logger = logging.getLogger(__name__)


class PostExplainerAgent:
    """Agent for explaining posts with context and citations."""
    
    def __init__(self):
        logger.info("Initializing PostExplainerAgent")
        self.model_router = ModelRouter()
        self.vector_store = VectorStore()
        self.web_search = WebSearch()
        self.external_sources = ExternalSourcesSearch()
        self.moderation = ModerationGuardrail()
    
    async def initialize(self):
        """Initialize agent components."""
        logger.info("Initializing vector store...")
        await self.vector_store.initialize()
        logger.info("✓ PostExplainerAgent fully initialized")
    
    async def explain_post(self, post_content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Explain a social media post with retrieval + synthesis.

        Returns:
        - explanation: 3-5 bullets with citations like [S1]
        - sources: list of structured sources shown in the UI
        - image_analysis: optional vision result
        """
        logger.info(f"Starting explain_post workflow for post ({len(post_content)} chars)")
        
        # Step 1: Input guardrail - Block non-compliant content
        moderation_result = await self._input_guardrail(post_content)
        if moderation_result.get("flagged"):
            error_msg = f"❌ Input not compliant ({moderation_result.get('category')}): {moderation_result.get('reason', 'Content violates policy')}. Please change your query and try again."
            logger.warning(f"✗ Step 1: Input blocked - {error_msg}")
            raise ValueError(error_msg)
        
        try:
            image_analysis = None
            if image_url:
                try:
                    image_analysis = await self.model_router.analyze_image(
                        image_url,
                        "Describe the image and identify any entities, memes, or text that provide context for the post.",
                    )
                except Exception as e:
                    logger.warning(f"Image analysis failed, continuing without it: {e}")

            sources = await build_sources_for_post(
                post_content=post_content,
                vector_store=self.vector_store,
                web_search=self.web_search,
                external_sources=self.external_sources,
                model_router=self.model_router,
                top_k=10,
            )

            sources_block = format_sources_for_prompt(sources)
            image_block = f"\n\nImage analysis (may be empty):\n{image_analysis}" if image_analysis else ""

            system = (
                "You explain social media posts by adding missing context. "
                "Only use the provided sources; do not invent facts. "
                "Write 3-5 concise bullet points. "
                "Each bullet must end with 1-3 citations like [S1] or [S2][S3] that support the claim; "
                "if a claim is general background from common knowledge, cite the closest supporting source anyway."
            )
            user = (
                f"Post:\n{post_content}\n\n"
                f"Sources:\n{sources_block}\n"
                f"{image_block}\n\n"
                "Return only the bullets, one per line starting with '- '."
            )

            explanation_text = await self.model_router.generate_completion(
                [{"role": "system", "content": system}, {"role": "user", "content": user}]
            )

            explanation_bullets = [
                line.strip()
                for line in (explanation_text or "").splitlines()
                if line.strip().startswith("- ")
            ]

            # Fallback: if the model didn't format bullets, coerce a single bullet.
            if not explanation_bullets and (explanation_text or "").strip():
                explanation_bullets = [f"- {(explanation_text or '').strip()}"]

            # Enforce 3-5 bullets for API contract / UI expectations.
            if len(explanation_bullets) > 5:
                explanation_bullets = explanation_bullets[:5]
            if 0 < len(explanation_bullets) < 3:
                # Duplicate last bullet to hit minimum, rather than re-calling the LLM.
                while len(explanation_bullets) < 3:
                    explanation_bullets.append(explanation_bullets[-1])

            full_text = " ".join(explanation_bullets)
            output_check = await self._output_guardrail(full_text)
            if output_check.get("flagged"):
                error_msg = f"❌ Generated content not compliant ({output_check.get('category')}): {output_check.get('reason', 'Content violates policy')}. Please change your query and try again."
                logger.warning(f"✗ Output blocked - {error_msg}")
                raise ValueError(error_msg)

            return {
                "explanation": explanation_bullets,
                "sources": sources,
                "image_analysis": image_analysis,
            }
            
        except Exception as e:
            logger.error(f"✗ Agent workflow error: {e}", exc_info=True)
            raise
    
    async def _input_guardrail(self, text: str) -> dict:
        """Step 1: Check input for policy violations."""
        result = await self.moderation.check_input(text)
        return result
    
    async def _output_guardrail(self, text: str) -> dict:
        """Step 6: Check generated content for policy violations."""
        result = await self.moderation.check_output(text)
        return result
