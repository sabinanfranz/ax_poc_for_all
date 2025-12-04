"""JobRun and JobResearch result models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional


@dataclass
class JobRun:
    """Represents a single job run request."""

    id: int | None
    company_name: str
    job_title: str
    industry_context: str | None
    business_goal: str | None
    manual_jd_text: str | None
    status: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class JobResearchResult:
    """Represents the output of Stage 0 Job Research."""

    job_run_id: int
    raw_job_desc: str
    research_sources: List[dict[str, Any]]


@dataclass
class JobResearchCollectResult:
    """Represents the output of Stage 0.1 Web Research Collector."""

    job_run_id: int
    raw_sources: List[dict[str, Any]]
    job_meta: Optional[dict[str, Any]] = None
