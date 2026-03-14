"""Core agent for explaining social media posts."""

from typing import Dict, List, Optional, Any
from app.models.schemas import Source
from app.llm.model_router import ModelRouter
from app.retrieval.vector_store import VectorStore
from app.retrieval.web_search import WebSearch
from app.guardrails.moderation import ModerationGuardrail
from app.observability.phoenix_tracing import PhoenixTracer
from app.config import settings


class PostExplainerAgent:
    """6-step agent for explaining posts with context and citations."""
    
    def __init__(self):
        self.model_router = ModelRouter()
        self.vector_store = VectorStore()
        self.web_search = WebSearch()
        self.moderation = ModerationGuardrail()
        self.tracer = PhoenixTracer(settings.phoenix_enabled)
    
    async def initialize(self):
        """Initialize agent components."""
        await self.vector_store.initialize()
    
    async def explain_post(self, post_content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Explain a social media post using 6-step agent workflow.
        
        Steps:
        1. Input guardrail - Check for policy violations
        2. Retrieve context - Query vector store and web search
        3. Analyze image - If provided, extract visual context
        4. Rank context - Rerank by relevance score
        5. Generate explanation - LLM creates explanation with citations
        6. Output guardrail - Check generated content
        """
        
        # Step 1: Input guardrail
        moderation_result = await self._input_guardrail(post_content)
        if moderation_result.get("flagged"):
            raise ValueError(f"Input flagged for moderation: {moderation_result.get('categories')}")
        
        # Step 2: Retrieve context
        sources = await self._retrieve_context(post_content)
        
        # Step 3: Analyze image (if provided)
        image_analysis = None
        if image_url:
            image_analysis = await self._analyze_image(image_url)
        
        # Step 4: Rerank context
        sources = await self._rerank_context(post_content, sources)
        
        # Step 5: Generate explanation
        explanation_bullets = await self._generate_explanation(post_content, sources, image_analysis)
        
        # Step 6: Output guardrail
        full_text = " ".join(explanation_bullets)
        output_check = await self._output_guardrail(full_text)
        if output_check.get("flagged"):
            raise ValueError(f"Output flagged for moderation: {output_check.get('categories')}")
        
        return {
            "explanation": explanation_bullets,
            "sources": sources,
            "image_analysis": image_analysis,
            "traces": self.tracer.export_traces()
        }
    
    async def _input_guardrail(self, text: str) -> dict:
        """Step 1: Check input for policy violations."""
        result = await self.moderation.check_input(text)
        self.tracer.log_moderation(text, result.get("flagged", False), result.get("categories", {}))
        return result
    
    async def _retrieve_context(self, query: str) -> List[Source]:
        """Step 2: Retrieve context from vector store and web search."""
        # Vector store search
        vector_results = await self.vector_store.search(query, k=settings.top_k_documents)
        
        # Web search
        web_results = await self.web_search.search(query, num_results=3)
        
        # Convert to Source objects
        sources = []
        for doc, distance in vector_results:
            sources.append(Source(
                title=doc.get("title", "Unknown Source"),
                context=doc.get("content", ""),
                relevance_score=1.0 - (distance / 100.0),  # Normalize L2 distance
                url=doc.get("url")
            ))
        
        for result in web_results:
            sources.append(Source(
                title=result.get("title", "Web Result"),
                context=result.get("snippet", ""),
                relevance_score=0.7,  # Default web score
                url=result.get("url")
            ))
        
        self.tracer.log_retrieval(query, len(sources), sources[0].relevance_score if sources else None)
        return sources
    
    async def _analyze_image(self, image_url: str) -> str:
        """Step 3: Analyze image for visual context."""
        analysis = await self.model_router.analyze_image(
            image_url,
            "Briefly describe the visual content and its relevance to social media context."
        )
        return analysis
    
    async def _rerank_context(self, query: str, sources: List[Source]) -> List[Source]:
        """Step 4: Rerank sources by relevance."""
        # Sort by relevance score
        reranked = sorted(sources, key=lambda s: s.relevance_score, reverse=True)
        
        # Keep top K
        reranked = reranked[:settings.rerank_top_k]
        
        self.tracer.log_agent_step("rerank_context", {"query": query, "sources_in": len(sources)}, {"sources_out": len(reranked)})
        
        return reranked
    
    async def _generate_explanation(self, post: str, sources: List[Source], image_analysis: Optional[str] = None) -> List[str]:
        """Step 5: Generate explanation with citations."""
        # Build context string
        context_text = "\n".join([
            f"- {s.title}: {s.context} (Score: {s.relevance_score:.2f})"
            for s in sources
        ])
        
        # Build prompt
        system_prompt = "You are an AI assistant that explains social media posts by providing context-grounded explanations with citations."
        
        user_prompt = f"""Explain the following social media post in 3-5 bullet points, citing the provided context sources.

Post: {post}

{"Image Analysis: " + image_analysis if image_analysis else ""}

Context Sources:
{context_text}

Provide concise, informative bullet points that explain the post using the context."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Generate explanation
        response = await self.model_router.generate_completion(messages)
        self.tracer.log_llm_call(settings.openai_model, messages, response)
        
        # Parse response into bullet points
        bullets = [line.strip() for line in response.split('\n') if line.strip() and line.strip().startswith('-')]
        
        self.tracer.log_agent_step("generate_explanation", {"context_sources": len(sources)}, {"explanation_bullets": len(bullets)})
        
        return bullets if bullets else [response]
    
    async def _output_guardrail(self, text: str) -> dict:
        """Step 6: Check generated content for policy violations."""
        result = await self.moderation.check_output(text)
        self.tracer.log_moderation(text, result.get("flagged", False), result.get("categories", {}))
        return result
