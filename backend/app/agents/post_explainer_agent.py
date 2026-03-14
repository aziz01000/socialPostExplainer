"""Post Explainer Agent using LangGraph."""

import logging
import time
from typing import cast

from app.guardrails import moderation_client
from app.llm import model_router
from app.models import AgentState, Source
from app.observability import tracer
from app.retrieval import vector_store, web_search_retriever

logger = logging.getLogger(__name__)


class PostExplainerAgent:
    """LangGraph-style agent for explaining social media posts."""

    def __init__(self):
        """Initialize the agent."""
        self.state: dict = {}

    async def run(self, post: str, image_url: str = None) -> AgentState:
        """Run the agent pipeline.

        Args:
            post: Social media post text
            image_url: Optional image URL

        Returns:
            Final agent state with explanation and sources
        """
        # Initialize state
        state = AgentState(post=post, image_url=image_url)

        # Step 1: Input Guardrail
        state = await self._input_guardrail(state)
        if not state.moderation_input_safe:
            logger.warning("Input failed moderation check")
            return state

        # Step 2: Retrieve Context (hybrid retrieval)
        state = await self._retrieve_context(state)

        # Step 3: Analyze Image (if provided)
        if image_url:
            state = await self._analyze_image(state)

        # Step 4: Rerank Context
        state = await self._rerank_context(state)

        # Step 5: Generate Explanation
        state = await self._generate_explanation(state)

        # Step 6: Output Guardrail
        state = await self._output_guardrail(state)

        return state

    async def _input_guardrail(self, state: AgentState) -> AgentState:
        """Check input for policy violations.

        Args:
            state: Agent state

        Returns:
            Updated state with moderation result
        """
        logger.info("Running input guardrail check")
        start_time = time.time()

        try:
            is_safe, _ = await moderation_client.check_input(state.post)
            state.moderation_input_safe = is_safe

            if not is_safe:
                state.error = "Input content violates content policy"

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step("input_guardrail", state.model_dump(), latency_ms)

            return state

        except Exception as e:
            logger.error(f"Input guardrail failed: {str(e)}")
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "input_guardrail", state.model_dump(), latency_ms, error=str(e)
            )
            return state

    async def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context using hybrid retrieval.

        Args:
            state: Agent state

        Returns:
            Updated state with retrieval results
        """
        logger.info("Running retrieval step")
        start_time = time.time()

        try:
            # Vector search
            vector_results = await vector_store.search(state.post, top_k=3)

            # Web search
            web_results = await web_search_retriever.search(state.post, top_k=2)

            # Combine results
            all_results = vector_results + web_results

            # Convert to RetrievalResult format
            from app.models import RetrievalResult

            state.retrieval_results = [
                RetrievalResult(
                    document=r.get("text", ""),
                    source=r.get("title", r.get("source", "Unknown")),
                    relevance_score=r.get("relevance_score", 0.5),
                    url=r.get("source", None),
                )
                for r in all_results
            ]

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "retrieve_context", state.model_dump(), latency_ms
            )

            logger.info(f"Retrieved {len(state.retrieval_results)} documents")
            return state

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "retrieve_context", state.model_dump(), latency_ms, error=str(e)
            )
            return state

    async def _analyze_image(self, state: AgentState) -> AgentState:
        """Analyze image if provided.

        Args:
            state: Agent state

        Returns:
            Updated state with image analysis
        """
        if not state.image_url:
            return state

        logger.info("Analyzing image")
        start_time = time.time()

        try:
            analysis = await model_router.analyze_image(
                image_url=state.image_url,
                post=state.post,
            )
            state.image_analysis = analysis

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step("analyze_image", state.model_dump(), latency_ms)

            return state

        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "analyze_image", state.model_dump(), latency_ms, error=str(e)
            )
            return state

    async def _rerank_context(self, state: AgentState) -> AgentState:
        """Rerank retrieved documents by relevance.

        Args:
            state: Agent state

        Returns:
            Updated state with reranked results
        """
        logger.info("Reranking context")
        start_time = time.time()

        try:
            # Sort by relevance score and take top-3
            sorted_results = sorted(
                state.retrieval_results,
                key=lambda x: x.relevance_score,
                reverse=True,
            )
            state.reranked_results = sorted_results[:3]

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step("rerank_context", state.model_dump(), latency_ms)

            logger.info(f"Reranked to top {len(state.reranked_results)} documents")
            return state

        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "rerank_context", state.model_dump(), latency_ms, error=str(e)
            )
            return state

    async def _generate_explanation(self, state: AgentState) -> AgentState:
        """Generate explanation using LLM with context.

        Args:
            state: Agent state

        Returns:
            Updated state with explanation
        """
        logger.info("Generating explanation")
        start_time = time.time()

        try:
            # Prepare context
            context = [r.document for r in state.reranked_results]

            # Generate explanation
            explanation, token_usage = await model_router.generate_explanation(
                post=state.post,
                context=context,
                image_analysis=state.image_analysis,
            )

            state.explanation = explanation

            # Build sources
            state.sources = [
                Source(
                    url=r.url or "Unknown",
                    title=r.source,
                    context=r.document[:100],
                )
                for r in state.reranked_results
            ]

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "generate_explanation", state.model_dump(), latency_ms
            )

            logger.info("Explanation generated successfully")
            return state

        except Exception as e:
            logger.error(f"Explanation generation failed: {str(e)}")
            state.error = "Failed to generate explanation"
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "generate_explanation", state.model_dump(), latency_ms, error=str(e)
            )
            return state

    async def _output_guardrail(self, state: AgentState) -> AgentState:
        """Check output for policy violations.

        Args:
            state: Agent state

        Returns:
            Updated state with output moderation result
        """
        logger.info("Running output guardrail check")
        start_time = time.time()

        try:
            is_safe, _ = await moderation_client.check_output(state.explanation)
            state.moderation_output_safe = is_safe

            if not is_safe:
                state.explanation = "The generated explanation was flagged for policy review."

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step("output_guardrail", state.model_dump(), latency_ms)

            return state

        except Exception as e:
            logger.error(f"Output guardrail failed: {str(e)}")
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_agent_step(
                "output_guardrail", state.model_dump(), latency_ms, error=str(e)
            )
            return state


# Global agent instance
post_explainer_agent = PostExplainerAgent()
