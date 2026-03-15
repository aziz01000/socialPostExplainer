"""LangGraph workflow for explaining social media posts."""

import logging
import re
import time
from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.tools import build_sources_for_post, format_sources_for_prompt
from app.graphs.state import ExplainState

logger = logging.getLogger(__name__)
_CITE_RE = re.compile(r"\[S\d+\]")


async def _node_moderation_input(state: ExplainState) -> ExplainState:
    """Run input moderation; set moderation_result and moderation_flagged."""
    agent = state["agent"]
    post_content = state["post_content"]
    result = await agent.moderation.check_input(post_content)
    flagged = bool(result.get("flagged"))
    return {
        "moderation_result": result,
        "moderation_flagged": flagged,
    }


async def _node_maybe_image(state: ExplainState) -> ExplainState:
    """Optionally run vision analysis if image_url is present."""
    agent = state["agent"]
    image_url = state.get("image_url")
    if not image_url:
        return {}
    try:
        t0 = time.time()
        image_analysis = await agent.model_router.analyze_image(
            image_url,
            "Describe the image with concrete details useful for retrieval: visible text, people, "
            "brands, products, logos, place names, and any meme/topic references.",
        )
        entry = {
            "tool": "vision.analyze_image",
            "input": {"image_url": image_url},
            "ms": int((time.time() - t0) * 1000),
            "output_preview": (image_analysis or "")[:280],
        }
    except Exception as e:
        logger.warning(f"Image analysis failed, continuing without it: {e}")
        image_analysis = None
        entry = {
            "tool": "vision.analyze_image",
            "input": {"image_url": image_url},
            "error": str(e),
        }
    return {
        "image_analysis": image_analysis,
        "tool_trace": [entry],
    }


async def _node_retrieve(state: ExplainState) -> ExplainState:
    """Retrieve and rerank sources (FAISS + web + external)."""
    agent = state["agent"]
    post_content = state["post_content"]
    image_analysis = state.get("image_analysis")
    tool_trace = state.get("tool_trace") or []
    sources = await build_sources_for_post(
        post_content=post_content,
        vector_store=agent.vector_store,
        web_search=agent.web_search,
        external_sources=agent.external_sources,
        model_router=agent.model_router,
        top_k=10,
        tool_trace=tool_trace,
        additional_search_context=image_analysis,
    )
    return {"sources": sources}


async def _node_generate(state: ExplainState) -> ExplainState:
    """Build prompt and call LLM for explanation."""
    agent = state["agent"]
    post_content = state["post_content"]
    sources = state["sources"]
    image_analysis = state.get("image_analysis")
    tool_trace = state.get("tool_trace") or []

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

    t_llm = time.time()
    explanation_text = await agent.model_router.generate_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    llm_entry = {
        "tool": "llm.generate_completion",
        "input_preview": {"system": system[:220], "user": user[:400]},
        "ms": int((time.time() - t_llm) * 1000),
        "output_preview": (explanation_text or "")[:500],
    }
    return {
        "explanation_text": explanation_text or "",
        "tool_trace": [llm_entry],
    }


async def _node_post_process(state: ExplainState) -> ExplainState:
    """Normalize bullets and enforce citations."""
    explanation_text = state.get("explanation_text") or ""
    sources = state.get("sources") or []

    explanation_bullets = [
        line.strip()
        for line in explanation_text.splitlines()
        if line.strip().startswith("- ")
    ]
    if not explanation_bullets and explanation_text.strip():
        explanation_bullets = [f"- {explanation_text.strip()}"]
    if len(explanation_bullets) > 5:
        explanation_bullets = explanation_bullets[:5]
    while len(explanation_bullets) < 3 and explanation_bullets:
        explanation_bullets.append(explanation_bullets[-1])

    if sources:
        fixed = []
        for b in explanation_bullets:
            if _CITE_RE.search(b):
                fixed.append(b)
            else:
                fixed.append(b.rstrip() + " [S1]")
        explanation_bullets = fixed

    return {"explanation_bullets": explanation_bullets}


async def _node_moderation_output(state: ExplainState) -> ExplainState:
    """Run output moderation on the generated text."""
    agent = state["agent"]
    bullets = state.get("explanation_bullets") or []
    full_text = " ".join(bullets)
    result = await agent.moderation.check_output(full_text)
    return {"output_moderation_flagged": bool(result.get("flagged"))}


def _route_after_moderation(state: ExplainState) -> Literal["maybe_image", "__end__"]:
    if state.get("moderation_flagged"):
        return "__end__"
    return "maybe_image"


def _route_after_output_moderation(state: ExplainState) -> Literal["__end__"]:
    return "__end__"


def create_explain_graph():
    """Build and compile the post explainer StateGraph."""
    graph = StateGraph(ExplainState)

    graph.add_node("moderation_input", _node_moderation_input)
    graph.add_node("maybe_image", _node_maybe_image)
    graph.add_node("retrieve", _node_retrieve)
    graph.add_node("generate", _node_generate)
    graph.add_node("post_process", _node_post_process)
    graph.add_node("moderation_output", _node_moderation_output)

    graph.set_entry_point("moderation_input")
    graph.add_conditional_edges(
        "moderation_input",
        _route_after_moderation,
        {"maybe_image": "maybe_image", "__end__": END},
    )
    graph.add_edge("maybe_image", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "post_process")
    graph.add_edge("post_process", "moderation_output")
    graph.add_edge("moderation_output", END)

    return graph.compile()
