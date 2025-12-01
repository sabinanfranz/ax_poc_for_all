"""Stage 0 Job Research business logic."""

from __future__ import annotations

from typing import Optional

from ax_agent_factory.infra import db, llm_client
from ax_agent_factory.models.job_run import JobResearchResult, JobRun


def run_job_research(job_run: JobRun, manual_jd_text: Optional[str] = None) -> JobResearchResult:
    """Run Stage 0 Job Research, persist, and return the result."""
    llm_output = llm_client.call_gemini_job_research(
        company_name=job_run.company_name,
        job_title=job_run.job_title,
        manual_jd_text=manual_jd_text,
    )

    if job_run.id is None:
        raise ValueError("JobRun id is required to save research results.")

    result = JobResearchResult(
        job_run_id=job_run.id,
        raw_job_desc=llm_output.get("raw_job_desc", ""),
        research_sources=llm_output.get("research_sources", []),
    )

    db.save_job_research_result(result)
    return result
