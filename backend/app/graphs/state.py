"""State types for LangGraph workflows."""

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from app.models.schemas import Source


class ExplainState(TypedDict, total=False):
    """State for the post explainer graph."""

    post_content: str
    image_url: Optional[str]
    sources_type: str
    agent: Any  # PostExplainerAgent (injected at invoke)
    tool_trace: Annotated[List[Dict[str, Any]], operator.add]
    moderation_result: Dict[str, Any]
    moderation_flagged: bool
    image_analysis: Optional[str]
    sources: List[Source]
    explanation_text: str
    explanation_bullets: List[str]
    output_moderation_flagged: bool
    error: Optional[str]


class QAState(TypedDict, total=False):
    """State for the social QA graph."""

    question: str
    sources_type: str
    agent: Any  # SocialMediaQAAgent (injected at invoke)
    tool_trace: Annotated[List[Dict[str, Any]], operator.add]
    moderation_result: Dict[str, Any]
    moderation_flagged: bool
    sources: List[Source]
    answer_text: str
    output_moderation_flagged: bool
    platforms: Dict[str, int]
    error: Optional[str]
