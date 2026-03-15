"""Arize Phoenix tracing for LLM observability.

When phoenix_enabled, every LLM call (chat, embeddings, moderation, vision) is traced
and sent to Phoenix. Uses OpenTelemetry + OpenInference span kinds (LLM, EMBEDDING, GUARDRAIL).
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_tracer_provider = None
_tracer = None


def init_phoenix() -> bool:
    """Register Phoenix OTEL and get tracer. Call once at app startup. Returns True if enabled."""
    global _tracer_provider, _tracer
    if not getattr(settings, "phoenix_enabled", True):
        logger.info("Phoenix tracing disabled (phoenix_enabled=False)")
        return False
    try:
        from phoenix.otel import register

        kwargs = {
            "project_name": getattr(settings, "phoenix_project_name", "contextual-post-explainer"),
            "auto_instrument": False,  # we use manual spans (httpx-based OpenAI client)
        }
        endpoint = getattr(settings, "phoenix_collector_endpoint", None)
        if endpoint:
            kwargs["endpoint"] = endpoint if endpoint.endswith("/v1/traces") else f"{endpoint.rstrip('/')}/v1/traces"
        _tracer_provider = register(**kwargs)
        _tracer = _tracer_provider.get_tracer("app.observability.phoenix_tracing", "1.0.0")
        logger.info("✓ Phoenix tracing initialized (Arize Phoenix)")
        return True
    except Exception as e:
        logger.warning(f"Phoenix tracing not available: {e}")
        _tracer_provider = None
        _tracer = None
        return False


def get_phoenix_tracer():
    """Return the Phoenix OpenInference tracer, or None if disabled/unavailable."""
    return _tracer


def is_phoenix_enabled() -> bool:
    """Return True if Phoenix is enabled and tracer is available."""
    return getattr(settings, "phoenix_enabled", True) and _tracer is not None


@asynccontextmanager
async def trace_request(name: str, input_preview: str = ""):
    """
    Start a root span for the whole request. All LLM/embedding/guardrail spans
    created inside this context become children, so Phoenix shows one root per request.
    """
    tracer = get_phoenix_tracer()
    if not tracer:
        yield
        return
    try:
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        yield
        return
    ctx = tracer.start_as_current_span(name, openinference_span_kind="chain")
    span = ctx.__enter__()
    try:
        if input_preview and hasattr(span, "set_input"):
            span.set_input(input_preview[:500])
        elif input_preview and hasattr(span, "set_attribute"):
            span.set_attribute("input.value", input_preview[:500])
        yield span
        span.set_status(Status(StatusCode.OK))
    except Exception as e:
        if hasattr(span, "record_exception"):
            span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR))
        raise
    finally:
        ctx.__exit__(None, None, None)


@asynccontextmanager
async def trace_llm(
    name: str,
    model_name: str,
    input_messages: List[Dict[str, Any]],
    invocation_parameters: Optional[Dict[str, Any]] = None,
):
    """Context manager to trace an LLM (chat completion) call. Yields (span, set_output)."""
    noop = lambda *_args, **_kwargs: None
    tracer = get_phoenix_tracer()
    if not tracer:
        yield None, noop
        return
    try:
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        yield None, noop
        return
    ctx = tracer.start_as_current_span(name, openinference_span_kind="llm")
    span = ctx.__enter__()
    try:
        if hasattr(span, "set_input"):
            span.set_input(input_messages)
        else:
            span.set_attribute("input.value", json.dumps([{"role": m.get("role"), "content_preview": str(m.get("content", ""))[:200]} for m in input_messages]))
        if model_name and hasattr(span, "set_attribute"):
            span.set_attribute("llm.model_name", model_name)
        if invocation_parameters and hasattr(span, "set_attribute"):
            span.set_attribute("llm.invocation_parameters", json.dumps(invocation_parameters))
        def set_output(value: Any, token_usage: Optional[Dict[str, int]] = None) -> None:
            if hasattr(span, "set_output"):
                span.set_output(value)
            else:
                span.set_attribute("output.value", value if isinstance(value, str) else json.dumps(value)[:2000])
            if token_usage and hasattr(span, "set_attribute"):
                prompt_tokens = token_usage.get("prompt_tokens", 0) or 0
                completion_tokens = token_usage.get("completion_tokens", 0) or 0
                total_tokens = token_usage.get("total_tokens", 0) or (prompt_tokens + completion_tokens)
                span.set_attribute("llm.token_count.prompt", prompt_tokens)
                span.set_attribute("llm.token_count.completion", completion_tokens)
                span.set_attribute("llm.token_count.total", total_tokens)
            span.set_status(Status(StatusCode.OK))
        yield span, set_output
    except Exception as e:
        if hasattr(span, "record_exception"):
            span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR))
        raise
    finally:
        ctx.__exit__(None, None, None)


@asynccontextmanager
async def trace_embedding(
    name: str,
    model_name: str,
    input_texts: List[str],
):
    """Context manager to trace an embedding call."""
    noop = lambda *_args, **_kwargs: None
    tracer = get_phoenix_tracer()
    if not tracer:
        yield None, noop
        return
    try:
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        yield None, noop
        return
    ctx = tracer.start_as_current_span(name, openinference_span_kind="embedding")
    span = ctx.__enter__()
    try:
        inp = json.dumps({"texts_count": len(input_texts), "preview": (input_texts[0][:200] + "..." if input_texts and len(input_texts[0]) > 200 else (input_texts[0] if input_texts else ""))})
        if hasattr(span, "set_input"):
            span.set_input(inp)
        else:
            span.set_attribute("input.value", inp)
        if model_name and hasattr(span, "set_attribute"):
            span.set_attribute("llm.model_name", model_name)
        def set_output(value: Any) -> None:
            out = json.dumps({"embeddings_count": len(value) if isinstance(value, list) else "?"})
            if hasattr(span, "set_output"):
                span.set_output(out)
            else:
                span.set_attribute("output.value", out)
            span.set_status(Status(StatusCode.OK))
        yield span, set_output
    except Exception as e:
        if hasattr(span, "record_exception"):
            span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR))
        raise
    finally:
        ctx.__exit__(None, None, None)


@asynccontextmanager
async def trace_guardrail(
    name: str,
    input_preview: str,
):
    """Context manager to trace a guardrail/moderation call."""
    noop = lambda *_args, **_kwargs: None
    tracer = get_phoenix_tracer()
    if not tracer:
        yield None, noop
        return
    try:
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        yield None, noop
        return
    ctx = tracer.start_as_current_span(name, openinference_span_kind="guardrail")
    span = ctx.__enter__()
    try:
        inp = input_preview[:500] if input_preview else ""
        if hasattr(span, "set_input"):
            span.set_input(inp)
        else:
            span.set_attribute("input.value", inp)
        def set_output(value: Any) -> None:
            out = json.dumps(value) if isinstance(value, dict) else str(value)
            if hasattr(span, "set_output"):
                span.set_output(out)
            else:
                span.set_attribute("output.value", out[:2000])
            span.set_status(Status(StatusCode.OK))
        yield span, set_output
    except Exception as e:
        if hasattr(span, "record_exception"):
            span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR))
        raise
    finally:
        ctx.__exit__(None, None, None)


# Legacy in-memory tracer (optional, for tests/debug)
class PhoenixTracer:
    """In-memory tracer for observability (legacy). Use Phoenix OTEL for production."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.traces = []

    def log_llm_call(self, model: str, messages: list, response: str, tokens: Optional[int] = None) -> None:
        if not self.enabled:
            return
        self.traces.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "llm_call",
            "model": model,
            "messages_count": len(messages),
            "response_length": len(response),
            "tokens": tokens,
        })

    def log_retrieval(self, query: str, num_results: int, top_score: Optional[float] = None) -> None:
        if not self.enabled:
            return
        self.traces.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "retrieval",
            "query": query,
            "num_results": num_results,
            "top_score": top_score,
        })

    def log_moderation(self, text: str, flagged: bool, categories: Dict) -> None:
        if not self.enabled:
            return
        self.traces.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "moderation",
            "text_length": len(text),
            "flagged": flagged,
            "categories": categories,
        })

    def log_agent_step(self, step_name: str, input_data: Any, output_data: Any) -> None:
        if not self.enabled:
            return
        self.traces.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "agent_step",
            "step_name": step_name,
            "input_keys": list(input_data.keys()) if isinstance(input_data, dict) else None,
            "output_keys": list(output_data.keys()) if isinstance(output_data, dict) else None,
        })

    def export_traces(self) -> list:
        return self.traces.copy()
