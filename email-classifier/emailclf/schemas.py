"""Data shapes used across the project.

Pydantic models are used for anything that comes back from an LLM, because LLM
output is unpredictable text. We never trust it until Pydantic has validated it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LLMClassification(BaseModel):
    """The JSON object we ask the LLM to return for classification."""

    # Literal = the model may ONLY return one of these strings, otherwise
    # validation fails and we retry. (tests/test_schemas.py checks this stays
    # in sync with config.LABELS.)
    label: Literal["spam", "job_offer", "job_task", "job_confirmation", "job_rejection"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class JobEmailInfo(BaseModel):
    """Structured facts pulled out of a job-related email."""

    company: Optional[str] = None
    role: Optional[str] = None
    deadline: Optional[str] = None  # kept as text: "Friday 29 Nov", "within 5 days"
    action_items: list[str] = Field(default_factory=list)


@dataclass
class Prediction:
    """What the pipeline returns for one email."""

    label: str  # one of LABELS, or "needs_review"
    confidence: float  # 0..1
    source: str  # "baseline" | "llm" | "rule:<name>" | "injection_guard" | "llm_error"
    raw_label: str  # the best guess BEFORE the threshold turned it into needs_review
    latency_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    notes: list[str] = field(default_factory=list)
