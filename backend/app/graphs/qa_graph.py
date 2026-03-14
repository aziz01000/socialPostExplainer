"""LangGraph workflow for social media Q&A."""

import logging
import time
from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.tools import build_sources_for_post, format_sources_for_prompt
from app.graphs.state import QAState

logger = logging.getLogger(__name__)


async def _node_moderation_input(state: QAState) -> QAState:
    """Run input moderation on the question."""
    agent = state["agent"]
    question = state["question"]
    result = await agent.moderation.check_input(question)
    return {
        "moderation_result": result,
        "moderation_flagged": bool(result.get("flagged")),
    }


async def _node_retrieve(state: QAState) -> QAState:
    """Retrieve sources (FAISS + web + external) for the question."""
    agent = state["agent"]
    question = state["question"]
    sources_type = state.get("sources_type") or "all"
    tool_trace = state.get("tool_trace") or []

    sources = await build_sources_for_post(
        post_content=question,
        vector_store=agent.vector_store,
        web_search=agent.web_search,
        external_sources=agent.external_sources,
        model_router=agent.model_router,
        top_k=12,
        sources_type=sources_type,
        tool_trace=tool_trace,
    )
    return {"sources": sources}


async def _node_generate(state: QAState) -> QAState:
    """Build prompt and call LLM for answer."""
    agent = state["agent"]
    question = state["question"]
    sources = state["sources"]
    tool_trace = state.get("tool_trace") or []

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

    t_llm = time.time()
    answer_text = await agent.model_router.generate_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    llm_entry = {
        "tool": "llm.generate_completion",
        "input_preview": {"system": system[:220], "user": user[:400]},
        "ms": int((time.time() - t_llm) * 1000),
        "output_preview": (answer_text or "")[:500],
    }
    return {
        "answer_text": answer_text or "",
        "tool_trace": [llm_entry],
    }


async def _node_moderation_output(state: QAState) -> QAState:
    """Run output moderation on the generated answer."""
    agent = state["agent"]
    answer_text = state.get("answer_text") or ""
    result = await agent.moderation.check_output(answer_text)
    return {"output_moderation_flagged": bool(result.get("flagged"))}


async def _node_build_breakdown(state: QAState) -> QAState:
    """Compute platform breakdown for sources."""
    sources = state.get("sources") or []
    platforms = {}
    for s in sources:
        p = (s.platform or "unknown").lower()
        platforms[p] = platforms.get(p, 0) + 1
    return {"platforms": platforms}


def _route_after_moderation(state: QAState) -> Literal["retrieve", "__end__"]:
    if state.get("moderation_flagged"):
        return "__end__"
    return "retrieve"


def create_qa_graph():
    """Build and compile the social QA StateGraph."""
    graph = StateGraph(QAState)

    graph.add_node("moderation_input", _node_moderation_input)
    graph.add_node("retrieve", _node_retrieve)
    graph.add_node("generate", _node_generate)
    graph.add_node("moderation_output", _node_moderation_output)
    graph.add_node("build_breakdown", _node_build_breakdown)

    graph.set_entry_point("moderation_input")
    graph.add_conditional_edges(
        "moderation_input",
        _route_after_moderation,
        {"retrieve": "retrieve", "__end__": END},
    )
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "moderation_output")
    graph.add_edge("moderation_output", "build_breakdown")
    graph.add_edge("build_breakdown", END)

    return graph.compile()
