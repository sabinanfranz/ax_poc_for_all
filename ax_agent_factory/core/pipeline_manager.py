"""Pipeline orchestrator for AX Agent Factory stages."""

from __future__ import annotations

from typing import Optional

from ax_agent_factory.core import research
from ax_agent_factory.core.ivc.pipeline import run_ivc_pipeline
from ax_agent_factory.core.schemas.common import JobInput, JobMeta
from ax_agent_factory.models.job_run import JobResearchResult, JobRun
from ax_agent_factory.models.stages import PIPELINE_STAGES, StageMeta
from ax_agent_factory.infra import db


class PipelineManager:
    """Manage stage execution and caching across the pipeline."""

    def __init__(self) -> None:
        self.stages = sorted(PIPELINE_STAGES, key=lambda s: s.order)

    def create_or_get_job_run(self, company_name: str, job_title: str) -> JobRun:
        """Create a new JobRun (PoC: always create fresh)."""
        return db.create_job_run(company_name, job_title)

    def run_stage_0_job_research(
        self,
        job_run: JobRun,
        manual_jd_text: Optional[str] = None,
        *,
        force_rerun: bool = False,
    ) -> JobResearchResult:
        """
        Run Stage 0: Job Research. Uses cached DB result unless force_rerun is True.
        """
        if job_run.id is None:
            raise ValueError("JobRun must have an id before running stages.")

        if not force_rerun:
            cached = db.get_job_research_result(job_run.id)
            if cached:
                return cached

        return research.run_job_research(job_run, manual_jd_text=manual_jd_text)

    def run_stage_1_ivc(self, *args, **kwargs):  # pragma: no cover - stub
        job_run: JobRun = kwargs.get("job_run")
        job_research_result: Optional[JobResearchResult] = kwargs.get("job_research_result")

        if job_run is None:
            raise ValueError("job_run is required for Stage 1 IVC")
        if job_run.id is None:
            raise ValueError("job_run.id is required for Stage 1 IVC")

        if job_research_result is None:
            job_research_result = db.get_job_research_result(job_run.id)
        if job_research_result is None:
            raise ValueError("Job Research result not found; run Stage 0 first.")

        job_input = JobInput(
            job_meta=JobMeta(
                company_name=job_run.company_name,
                job_title=job_run.job_title,
                industry_context="",
                business_goal=None,
            ),
            raw_job_desc=job_research_result.raw_job_desc,
        )
        return run_ivc_pipeline(job_input, llm_client=kwargs.get("llm_client"))

    def run_stage_2_dna(self, *args, **kwargs):  # pragma: no cover - stub
        raise NotImplementedError("Stage 2 DNA not implemented yet.")

    def run_stage_3_workflow(self, *args, **kwargs):  # pragma: no cover - stub
        raise NotImplementedError("Stage 3 Workflow not implemented yet.")
