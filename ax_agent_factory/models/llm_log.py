"""Dataclass for LLM call logging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMCallLog:
    """Represents one LLM call entry for persistence."""

    created_at: str
    stage_name: str
    model_name: str
    input_payload_json: str
    status: str
    job_run_id: Optional[int] = None
    agent_name: Optional[str] = None
    prompt_version: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    output_text_raw: Optional[str] = None
    output_json_parsed: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
