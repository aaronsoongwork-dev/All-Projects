"""Structured extraction: pull company, role, deadline and action items out of job emails.

Uses the same "ask for JSON -> validate with Pydantic -> retry" loop as classification.
This is what turns the `job_task` class into a useful deadline list.
"""

from __future__ import annotations

from . import prompts
from .llm import LLMClient, StructuredResult, get_client, structured_call
from .schemas import JobEmailInfo


def extract_job_info(text: str, client: LLMClient | None = None) -> tuple[JobEmailInfo | None, StructuredResult]:
    client = client or get_client()
    res = structured_call(client, prompts.EXTRACTION_SYSTEM, prompts.extraction_user_message(text), JobEmailInfo)
    info = res.obj if isinstance(res.obj, JobEmailInfo) else None
    return info, res
