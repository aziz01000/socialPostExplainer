"""Agent helper functions.

Historically this file provided LangChain `@tool` wrappers. The current codebase
uses these helpers directly to avoid pulling in LangChain as a dependency.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import re
import numpy as np
import time
from app.retrieval.vector_store import VectorStore
from app.retrieval.web_search import WebSearch
from app.retrieval.social_media_search import ExternalSourcesSearch
from app.llm.model_router import ModelRouter
from app.models.schemas import Source
from app.config import settings

logger = logging.getLogger(__name__)

def _clean_post_for_query(text: str) -> str:
    # Strip obvious URLs and excessive whitespace; keep hashtags and mentions.
    t = re.sub(r"https?://\S+", "", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:500]


def _safe_truncate(text: str, limit: int = 500) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 1] + "…"


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


async def build_sources_for_post(
    *,
    post_content: str,
    vector_store: VectorStore,
    web_search: WebSearch,
    external_sources: ExternalSourcesSearch,
    model_router: ModelRouter,
    top_k: int = 8,
    sources_type: str = "all",
    tool_trace: Optional[List[Dict[str, Any]]] = None,
) -> List[Source]:
    """Retrieve and rerank sources for a post."""
    trace = tool_trace if tool_trace is not None else []
    query = _clean_post_for_query(post_content)

    # Retrieve in parallel.
    t0 = time.time()
    vector_task = vector_store.search(query, k=max(3, settings.top_k_documents))
    web_task = web_search.search(query, num_results=5)
    external_task = external_sources.search(query, num_results=5, sources_type=sources_type)

    vector_results, web_results, external_results = await asyncio.gather(
        vector_task, web_task, external_task, return_exceptions=True
    )
    trace.append(
        {
            "tool": "retrieve_all",
            "input": {"query": query, "sources_type": sources_type},
            "ms": int((time.time() - t0) * 1000),
        }
    )

    sources: List[Source] = []

    if not isinstance(vector_results, Exception):
        trace.append(
            {
                "tool": "vector_store.search",
                "input": {"query": query, "k": max(3, settings.top_k_documents)},
                "output_preview": [
                    {
                        "title": (doc or {}).get("title"),
                        "score": float(score),
                        "url": (doc or {}).get("url"),
                    }
                    for doc, score in (vector_results or [])[:5]
                ],
            }
        )
        for doc, score in (vector_results or []):
            sources.append(
                Source(
                    title=doc.get("title", "Document"),
                    context=_safe_truncate(doc.get("content", ""), 700),
                    relevance_score=float(score),
                    url=doc.get("url"),
                    platform="vector_db",
                    engagement_score=None,
                    author=None,
                )
            )
    else:
        trace.append(
            {
                "tool": "vector_store.search",
                "input": {"query": query, "k": max(3, settings.top_k_documents)},
                "error": str(vector_results),
            }
        )

    if not isinstance(web_results, Exception):
        trace.append(
            {
                "tool": "web_search.search",
                "input": {"query": query, "num_results": 5},
                "output_preview": [
                    {
                        "title": (r or {}).get("title"),
                        "url": (r or {}).get("url"),
                        "snippet": _safe_truncate((r or {}).get("snippet", ""), 140),
                    }
                    for r in (web_results or [])[:5]
                ],
            }
        )
        for r in (web_results or []):
            sources.append(
                Source(
                    title=r.get("title", "Web result"),
                    context=_safe_truncate(r.get("snippet", ""), 400),
                    relevance_score=0.5,
                    url=r.get("url"),
                    platform=r.get("platform") or "web",
                    engagement_score=None,
                    author=None,
                )
            )
    else:
        trace.append(
            {
                "tool": "web_search.search",
                "input": {"query": query, "num_results": 5},
                "error": str(web_results),
            }
        )

    if not isinstance(external_results, Exception):
        trace.append(
            {
                "tool": "external_sources.search",
                "input": {"query": query, "num_results": 5, "sources_type": sources_type},
                "output_preview": [
                    {
                        "platform": (r or {}).get("platform"),
                        "title": (r or {}).get("title"),
                        "score": float((r or {}).get("score", 0.0)),
                        "engagement": (r or {}).get("engagement"),
                        "url": (r or {}).get("url"),
                    }
                    for r in (external_results or [])[:5]
                ],
            }
        )
        for r in (external_results or []):
            sources.append(
                Source(
                    title=r.get("title", "External result"),
                    context=_safe_truncate(r.get("content", ""), 500),
                    relevance_score=float(r.get("score", 0.5)),
                    url=r.get("url"),
                    platform=r.get("platform") or "external",
                    engagement_score=r.get("engagement"),
                    author=r.get("author"),
                )
            )
    else:
        trace.append(
            {
                "tool": "external_sources.search",
                "input": {"query": query, "num_results": 5, "sources_type": sources_type},
                "error": str(external_results),
            }
        )

    # Rerank with embeddings if available.
    try:
        t1 = time.time()
        texts = [query] + [f"{s.title}\n{s.context}" for s in sources]
        embs = await model_router.generate_embeddings(texts)
        if not embs or len(embs) != len(texts):
            raise ValueError("embedding count mismatch")

        q = np.array(embs[0], dtype=np.float32)
        scored: List[Tuple[Source, float]] = []
        for s, e in zip(sources, embs[1:]):
            sim = _cosine_sim(q, np.array(e, dtype=np.float32))
            scored.append((s, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        reranked = []
        for s, sim in scored:
            s.relevance_score = max(0.0, min(1.0, float(sim)))
            reranked.append(s)
        sources = reranked
        trace.append(
            {
                "tool": "embedding_rerank",
                "input": {"items": len(texts) - 1},
                "ms": int((time.time() - t1) * 1000),
                "output_preview": [
                    {"title": s.title, "score": float(s.relevance_score)}
                    for s in sources[:5]
                ],
            }
        )
    except Exception as e:
        logger.warning(f"Embedding rerank unavailable, using provider scores. Error: {e}")
        sources.sort(key=lambda s: s.relevance_score, reverse=True)
        trace.append(
            {
                "tool": "embedding_rerank",
                "error": str(e),
                "note": "Falling back to provider/native scores",
            }
        )

    # Deduplicate by (title,url) to avoid repeating the same thing.
    seen = set()
    deduped = []
    for s in sources:
        key = (s.title or "", s.url or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)

    return deduped[: max(1, int(top_k))]


def format_sources_for_prompt(sources: List[Source]) -> str:
    """Format sources as numbered blocks so the model can cite them as [S1], [S2], ..."""
    lines: List[str] = []
    for i, s in enumerate(sources, 1):
        header = f"[S{i}] {s.title}"
        meta = []
        if s.platform:
            meta.append(f"platform={s.platform}")
        if s.url:
            meta.append(f"url={s.url}")
        if s.author:
            meta.append(f"author={s.author}")
        if s.engagement_score is not None:
            meta.append(f"engagement={s.engagement_score}")
        meta_str = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"{header}{meta_str}\n{(s.context or '').strip()}")
    return "\n\n".join(lines).strip()
