"""Stage 0 pipeline orchestrating collect → summarize."""

from __future__ import annotations

from typing import Optional

from ax_agent_factory.core.research.collector import run_job_research_collect
from ax_agent_factory.core.research.synthesizer import run_job_research_summarize
from ax_agent_factory.infra import db
from ax_agent_factory.models.job_run import JobResearchCollectResult, JobResearchResult, JobRun


def run_job_research(job_run: JobRun, manual_jd_text: Optional[str] = None) -> JobResearchResult:
    """
    Stage 0 pipeline:
      0.1 collect raw_sources (cacheable)
      0.2 synthesize raw_job_desc + research_sources (final output)
    """
    if job_run.id is None:
        raise ValueError("JobRun id is required to run Job Research.")

    collect_result = db.get_job_research_collect_result(job_run.id)
    if collect_result is None:
        collect_result = run_job_research_collect(job_run, manual_jd_text=manual_jd_text)

    return run_job_research_summarize(job_run, collect_result, manual_jd_text=manual_jd_text)
