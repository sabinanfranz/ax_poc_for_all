"""Stage 0.1 Web Research Collector."""

from __future__ import annotations

from typing import Optional

from ax_agent_factory.infra import db, llm_client
from ax_agent_factory.models.job_run import JobResearchCollectResult, JobRun


def run_job_research_collect(job_run: JobRun, manual_jd_text: Optional[str] = None) -> JobResearchCollectResult:
    """
    Run Stage 0.1: collect raw sources from web/JD.

    - Calls LLM (Gemini web_search) to gather raw_sources.
    - Persists the raw_sources payload for reuse.
    """
    if job_run.id is None:
        raise ValueError("JobRun id is required to save research collect results.")

    job_meta = {
        "company_name": job_run.company_name,
        "job_title": job_run.job_title,
        "industry_context": job_run.industry_context,
        "business_goal": job_run.business_goal,
    }

    llm_output = llm_client.call_job_research_collect(
        company_name=job_run.company_name,
        job_title=job_run.job_title,
        manual_jd_text=manual_jd_text,
        job_run_id=job_run.id,
    )

    result = JobResearchCollectResult(
        job_run_id=job_run.id,
        job_meta=job_meta,
        raw_sources=llm_output.get("raw_sources", []),
    )

    # Attach debug info for UI (not persisted)
    if "_raw_text" in llm_output:
        result.llm_raw_text = llm_output.get("_raw_text")  # type: ignore[attr-defined]
    elif "raw_text" in llm_output:
        result.llm_raw_text = llm_output.get("raw_text")  # type: ignore[attr-defined]
    if "_cleaned_json" in llm_output:
        result.llm_cleaned_json = llm_output.get("_cleaned_json")  # type: ignore[attr-defined]
    if "llm_error" in llm_output:
        result.llm_error = llm_output.get("llm_error")  # type: ignore[attr-defined]

    db.save_job_research_collect_result(result)
    return result
