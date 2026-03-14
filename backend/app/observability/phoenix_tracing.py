"""Observability and tracing."""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class PhoenixTracer:
    """Custom tracer for observability."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.traces = []
    
    def log_llm_call(self, model: str, messages: list, response: str, tokens: Optional[int] = None) -> None:
        """Log LLM API call."""
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "llm_call",
            "model": model,
            "messages_count": len(messages),
            "response_length": len(response),
            "tokens": tokens
        }
        self.traces.append(trace)
    
    def log_retrieval(self, query: str, num_results: int, top_score: Optional[float] = None) -> None:
        """Log retrieval operation."""
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "retrieval",
            "query": query,
            "num_results": num_results,
            "top_score": top_score
        }
        self.traces.append(trace)
    
    def log_moderation(self, text: str, flagged: bool, categories: Dict) -> None:
        """Log moderation check."""
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "moderation",
            "text_length": len(text),
            "flagged": flagged,
            "categories": categories
        }
        self.traces.append(trace)
    
    def log_agent_step(self, step_name: str, input_data: Any, output_data: Any) -> None:
        """Log agent step."""
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "agent_step",
            "step_name": step_name,
            "input_keys": list(input_data.keys()) if isinstance(input_data, dict) else None,
            "output_keys": list(output_data.keys()) if isinstance(output_data, dict) else None
        }
        self.traces.append(trace)
    
    def export_traces(self) -> list:
        """Export all traces."""
        return self.traces.copy()
