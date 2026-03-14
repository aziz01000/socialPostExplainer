"""Observability module."""

from .phoenix_tracing import PhoenixTracer, tracer

__all__ = ["tracer", "PhoenixTracer"]
