"""JobRun and JobResearch result models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List


@dataclass
class JobRun:
    """Represents a single job run request."""

    id: int | None
    company_name: str
    job_title: str
    created_at: datetime


@dataclass
class JobResearchResult:
    """Represents the output of Stage 0 Job Research."""

    job_run_id: int
    raw_job_desc: str
    research_sources: List[dict[str, Any]]
