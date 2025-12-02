"""Stage 0.2 Task-Oriented Synthesizer."""

from __future__ import annotations

from typing import Optional

from ax_agent_factory.infra import db, llm_client
from ax_agent_factory.models.job_run import JobResearchCollectResult, JobResearchResult, JobRun


def run_job_research_summarize(
    job_run: JobRun,
    collect_result: JobResearchCollectResult,
    manual_jd_text: Optional[str] = None,
) -> JobResearchResult:
    """
    Run Stage 0.2: synthesize raw_sources (+ manual JD) into raw_job_desc and research_sources.
    """
    if job_run.id is None:
        raise ValueError("JobRun id is required to save research results.")

    llm_output = llm_client.call_job_research_summarize(
        job_meta={
            "company_name": job_run.company_name,
            "job_title": job_run.job_title,
        },
        raw_sources=collect_result.raw_sources,
        manual_jd_text=manual_jd_text,
        job_run_id=job_run.id,
    )

    result = JobResearchResult(
        job_run_id=job_run.id,
        raw_job_desc=llm_output.get("raw_job_desc", ""),
        research_sources=llm_output.get("research_sources", []),
    )
    if "_raw_text" in llm_output:
        result.llm_raw_text = llm_output.get("_raw_text")  # type: ignore[attr-defined]
    elif "raw_text" in llm_output:
        result.llm_raw_text = llm_output.get("raw_text")  # type: ignore[attr-defined]
    if "_cleaned_json" in llm_output:
        result.llm_cleaned_json = llm_output.get("_cleaned_json")  # type: ignore[attr-defined]
    if "llm_error" in llm_output:
        result.llm_error = llm_output.get("llm_error")  # type: ignore[attr-defined]

    db.save_job_research_result(result)
    return result
