"""Agent for answering questions using FAISS + external sources (social media + news APIs)."""

import logging
from typing import Dict, List, Optional, Any
from app.models.schemas import Source
from app.llm.model_router import ModelRouter
from app.retrieval.vector_store import VectorStore
from app.retrieval.social_media_search import ExternalSourcesSearch
from app.config import settings

logger = logging.getLogger(__name__)


class SocialMediaQAAgent:
    """Question-answering agent combining FAISS + external sources (social media & news)."""
    
    def __init__(self):
        logger.info("Initializing SocialMediaQAAgent")
        self.model_router = ModelRouter()
        self.vector_store = VectorStore()
        self.external_sources = ExternalSourcesSearch()
    
    async def initialize(self):
        """Initialize agent components."""
        logger.info("Initializing vector store for QA agent...")
        await self.vector_store.initialize()
        logger.info("✓ SocialMediaQAAgent fully initialized")
    
    async def answer_question(self, question: str, sources_type: str = "all") -> Dict[str, Any]:
        """
        Answer a question using combined sources.
        
        Process:
        1. Search FAISS vector store for matching documents
        2. Search external sources (social media + news APIs)
        3. Combine and rank results
        4. Generate comprehensive answer with citations
        
        Args:
            question: The question to answer
            sources_type: 'all', 'social', or 'news'
        """
        logger.info(f"Answering question: '{question}' (source_type={sources_type})")
        
        # Step 1: Search FAISS
        logger.debug("Step 1: Searching FAISS vector store")
        faiss_results = await self._search_faiss(question)
        logger.info(f"✓ Step 1: FAISS returned {len(faiss_results)} results")
        
        # Step 2: Search external sources
        logger.debug(f"Step 2: Searching external sources ({sources_type})")
        external_results = await self._search_external_sources(question, sources_type)
        logger.info(f"✓ Step 2: External sources returned {len(external_results)} results")
        
        # Step 3: Combine and rank
        logger.debug("Step 3: Combining and ranking results")
        combined_sources = await self._combine_results(question, faiss_results, external_results)
        logger.info(f"✓ Step 3: Combined into {len(combined_sources)} ranked sources")
        
        # Step 4: Generate answer
        logger.debug("Step 4: Generating answer from sources")
        answer = await self._generate_answer(question, combined_sources)
        logger.info(f"✓ Step 4: Answer generated ({len(answer['summary'])} chars)")
        
        # Count by source type
        source_breakdown = self._get_source_breakdown(faiss_results, external_results, combined_sources)
        
        return {
            "question": question,
            "answer": answer,
            "sources": combined_sources,
            "source_breakdown": source_breakdown
        }
    
    async def _search_faiss(self, query: str) -> List[Source]:
        """Search FAISS vector store."""
        logger.debug(f"Querying FAISS for: {query}")
        try:
            results = await self.vector_store.search(query, k=settings.top_k_documents)
            sources = []
            for doc, relevance in results:
                sources.append(Source(
                    title=doc.get("title", "Unknown"),
                    context=doc.get("content", ""),
                    relevance_score=max(0.0, min(1.0, relevance)),
                    url=doc.get("url"),
                    platform="docs"
                ))
            logger.debug(f"FAISS returned {len(sources)} documents")
            return sources
        except Exception as e:
            logger.error(f"✗ FAISS search error: {e}", exc_info=True)
            return []
    
    async def _search_external_sources(self, query: str, sources_type: str) -> List[Source]:
        """Search external sources (social media + news APIs)."""
        logger.debug(f"Searching external sources ({sources_type}) for: {query}")
        try:
            results = await self.external_sources.search(query, num_results=5, sources_type=sources_type)
            sources = []
            for result in results:
                # Calculate relevance score based on engagement and source type
                base_score = result.get("score", 0.7)
                engagement = result.get("engagement", 0)
                engagement_boost = min(0.2, engagement / 1000)  # Cap boost at 0.2
                
                source = Source(
                    title=result.get("title", ""),
                    context=result.get("content", ""),
                    relevance_score=base_score + engagement_boost,
                    url=result.get("url"),
                    platform=result.get("platform", "external"),
                    engagement_score=engagement,
                    author=result.get("author", "")
                )
                
                # Add extra metadata
                source.source_type = result.get("source_type", "unknown")  # "social_media" or "news"
                source.published = result.get("published")
                
                sources.append(source)
            
            logger.debug(f"External sources returned {len(sources)} results")
            return sources
        except Exception as e:
            logger.error(f"✗ External sources search error: {e}", exc_info=True)
            return []
    
    async def _combine_results(self, query: str, faiss_results: List[Source], external_results: List[Source]) -> List[Source]:
        """Combine FAISS and external results with intelligent ranking."""
        logger.debug(f"Combining {len(faiss_results)} FAISS + {len(external_results)} external results")
        
        combined = []
        
        # Add FAISS results (higher base relevance for authoritative docs)
        for source in faiss_results:
            source.relevance_score = source.relevance_score * 1.2  # Boost for authoritative sources
            combined.append(source)
        
        # Add external results (diverse perspectives)
        for source in external_results:
            # Slightly boost news sources over social media
            if hasattr(source, 'source_type') and source.source_type == "news":
                source.relevance_score = source.relevance_score * 1.05
            combined.append(source)
        
        # Sort by relevance score
        combined = sorted(combined, key=lambda s: s.relevance_score, reverse=True)
        
        # Keep top results (combine based on quality)
        max_results = min(settings.rerank_top_k + 2, len(combined))
        combined = combined[:max_results]
        
        logger.debug(f"Final combined result count: {len(combined)}")
        return combined
    
    def _get_source_breakdown(self, faiss: List[Source], external: List[Source], combined: List[Source]) -> Dict:
        """Get breakdown of sources by type."""
        external_by_type = {}
        for source in external:
            if hasattr(source, 'source_type'):
                source_type = source.source_type
            else:
                source_type = "other"
            external_by_type[source_type] = external_by_type.get(source_type, 0) + 1
        
        # Count platforms within news/social
        platforms = {}
        for source in combined:
            platform = source.platform or "unknown"
            platforms[platform] = platforms.get(platform, 0) + 1
        
        return {
            "faiss_docs": len(faiss),
            "external_total": len(external),
            "external_breakdown": external_by_type,
            "combined_total": len(combined),
            "platforms": platforms
        }
    
    async def _generate_answer(self, question: str, sources: List[Source]) -> Dict[str, Any]:
        """Generate comprehensive answer using LLM."""
        logger.debug("Building context for LLM")
        
        # Build context from sources
        context_items = []
        for i, source in enumerate(sources, 1):
            platform = source.platform or 'unknown'
            source_type = getattr(source, 'source_type', 'unknown')
            published = getattr(source, 'published', '')
            published_str = f" ({published})" if published else ""
            
            item = f"{i}. [{platform.upper()}/{source_type}] {source.title}\n{source.context}\nRelevance: {source.relevance_score:.2f}{published_str}"
            context_items.append(item)
        
        context_text = "\n\n".join(context_items)
        
        # Build prompt
        system_prompt = """You are an expert analyst that synthesizes information from multiple sources 
(authoritative documents, social media discussions, and news articles) to provide comprehensive, balanced answers.
Cite specific sources when making claims. Acknowledge different perspectives from social media and news.
Structure answers with clear sections and bullet points. Indicate source types (docs, social, news) in citations."""
        
        user_prompt = f"""Based on the following sources (mix of documents, social media, and news), provide a comprehensive answer:

Question: {question}

Sources:
{context_text}

Please provide:
1. A direct answer (2-3 paragraphs)
2. Key insights from authoritative documents
3. Community perspectives (from social media)
4. Recent news coverage
5. Practical recommendations
6. Related topics worth exploring"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            logger.debug("Calling LLM for answer generation")
            response = await self.model_router.generate_completion(messages)
            logger.info(f"✓ LLM generated answer ({len(response)} chars)")
            
            return {
                "summary": response,
                "source_count": len(sources),
                "generated": True
            }
        except Exception as e:
            logger.error(f"✗ LLM answer generation failed: {e}", exc_info=True)
            
            # Fallback: synthesize from sources directly
            logger.info("Using fallback answer from source synthesis")
            fallback_answer = self._synthesize_fallback_answer(question, sources)
            
            return {
                "summary": fallback_answer,
                "source_count": len(sources),
                "generated": False,
                "note": "Generated from source synthesis (LLM unavailable)"
            }
    
    def _synthesize_fallback_answer(self, question: str, sources: List[Source]) -> str:
        """Generate answer without LLM by combining sources."""
        logger.debug("Synthesizing fallback answer from sources")
        
        # Extract by source type
        docs = [s for s in sources if s.platform == 'docs']
        news_sources = [s for s in sources if getattr(s, 'source_type', None) == 'news']
        social = [s for s in sources if getattr(s, 'source_type', None) == 'social_media']
        
        answer_parts = [
            f"Based on available sources regarding '{question}':\n"
        ]
        
        # Add document insights
        if docs:
            answer_parts.append("📚 Key Information from Documents:")
            for doc in docs[:2]:
                answer_parts.append(f"• {doc.title}: {doc.context[:150]}...")
        
        # Add news coverage
        if news_sources:
            answer_parts.append("\n📰 Recent News Coverage:")
            for article in news_sources[:2]:
                published = getattr(article, 'published', '')
                answer_parts.append(f"• {article.title} ({published})")
        
        # Add community perspectives
        if social:
            answer_parts.append("\n💬 Community Perspectives:")
            for post in social[:2]:
                engagement = getattr(post, 'engagement_score', 0)
                answer_parts.append(f"• {post.title} (Engagement: {engagement})")
        
        answer_parts.append(f"\nFound {len(sources)} relevant sources to answer your question.")
        
        return "\n".join(answer_parts)
    
    async def close(self):
        """Cleanup resources."""
        logger.info("Closing SocialMediaQAAgent")
        await self.external_sources.close()
