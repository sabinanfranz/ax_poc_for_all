"""Pipeline orchestrator for AX Agent Factory stages."""

from __future__ import annotations

from typing import Optional

from ax_agent_factory.core import research
from ax_agent_factory.core.ivc.phase_classifier import IVCPhaseClassifier
from ax_agent_factory.core.ivc.pipeline import run_ivc_pipeline
from ax_agent_factory.core.ivc.static_classifier import run_static_classifier
from ax_agent_factory.core.ivc.task_extractor import IVCTaskExtractor
from ax_agent_factory.core.schemas.common import IVCTaskListInput, JobInput, JobMeta
from ax_agent_factory.core.workflow import WorkflowMermaidRenderer, WorkflowStructPlanner, run_workflow
from ax_agent_factory.models.job_run import JobResearchResult, JobRun
from ax_agent_factory.models.stages import PIPELINE_STAGES, StageMeta
from ax_agent_factory.infra import db


class PipelineManager:
    """Manage stage execution and caching across the pipeline."""

    def __init__(self) -> None:
        self.stages = sorted(PIPELINE_STAGES, key=lambda s: (s.ui_group, s.ui_step))

    def create_or_get_job_run(
        self,
        company_name: str,
        job_title: str,
        manual_jd_text: Optional[str] = None,
        industry_context: Optional[str] = None,
        business_goal: Optional[str] = None,
    ) -> JobRun:
        """Create or fetch a JobRun with shared keys."""
        return db.create_or_get_job_run(
            company_name,
            job_title,
            manual_jd_text,
            industry_context=industry_context,
            business_goal=business_goal,
        )

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

    def run_stage_0_1_collect(self, job_run: JobRun, manual_jd_text: Optional[str] = None):
        if job_run.id is None:
            raise ValueError("JobRun id is required to run Stage 0.1")
        return research.run_job_research_collect(job_run, manual_jd_text=manual_jd_text)

    def run_stage_0_2_summarize(
        self,
        job_run: JobRun,
        collect_result=None,
        manual_jd_text: Optional[str] = None,
    ):
        if job_run.id is None:
            raise ValueError("JobRun id is required to run Stage 0.2")
        if collect_result is None:
            collect_result = db.get_job_research_collect_result(job_run.id)
        if collect_result is None:
            collect_result = research.run_job_research_collect(job_run, manual_jd_text=manual_jd_text)
        return research.run_job_research_summarize(job_run, collect_result, manual_jd_text=manual_jd_text)

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
                industry_context=job_run.industry_context or "",
                business_goal=job_run.business_goal,
            ),
            raw_job_desc=job_research_result.raw_job_desc,
        )
        return run_ivc_pipeline(job_input, llm_client=kwargs.get("llm_client"), job_run_id=job_run.id)

    def run_stage_1_1_task_extractor(self, job_run: JobRun, job_research_result: Optional[JobResearchResult] = None, *, llm_client=None):
        if job_run is None or job_run.id is None:
            raise ValueError("job_run is required for Stage 1.1")
        if job_research_result is None:
            job_research_result = db.get_job_research_result(job_run.id)
        if job_research_result is None:
            raise ValueError("Job Research result not found; run Stage 0 first.")
        job_input = JobInput(
            job_meta=JobMeta(
                company_name=job_run.company_name,
                job_title=job_run.job_title,
                industry_context=job_run.industry_context or "",
                business_goal=job_run.business_goal,
            ),
            raw_job_desc=job_research_result.raw_job_desc,
        )
        extractor = IVCTaskExtractor(llm_client=llm_client)
        result = extractor.run(job_input)
        try:
            db.save_task_atoms(job_run.id, result.task_atoms)
        except Exception:
            logger.exception("Failed to persist task_atoms for Stage 1.1")
        return result

    def run_stage_1_2_phase_classifier(
        self,
        job_run: JobRun,
        task_extraction_result=None,
        job_research_result: Optional[JobResearchResult] = None,
        *,
        llm_client=None,
    ):
        if job_run is None or job_run.id is None:
            raise ValueError("job_run is required for Stage 1.2")
        if job_research_result is None:
            job_research_result = db.get_job_research_result(job_run.id)
        if job_research_result is None:
            raise ValueError("Job Research result not found; run Stage 0 first.")
        if task_extraction_result is None:
            # Fall back to running extractor
            task_extraction_result = self.run_stage_1_1_task_extractor(
                job_run, job_research_result=job_research_result, llm_client=llm_client
            )
        classifier_input = IVCTaskListInput(
            job_meta=task_extraction_result.job_meta,
            raw_job_desc=job_research_result.raw_job_desc if job_research_result else "",
            task_atoms=task_extraction_result.task_atoms,
        )
        classifier = IVCPhaseClassifier(llm_client=llm_client)
        result = classifier.run(classifier_input)
        result.task_atoms = task_extraction_result.task_atoms
        try:
            db.apply_ivc_classification(job_run.id, result.ivc_tasks)
        except Exception:
            logger.exception("Failed to persist IVC classification for Stage 1.2")
        return result

    def run_stage_2_dna(self, *args, **kwargs):  # pragma: no cover - stub
        raise NotImplementedError("Stage 2 DNA not implemented yet.")

    def run_stage_1_3_static(
        self,
        *,
        job_run: JobRun,
        phase_result,
        llm_client=None,
    ):
        if job_run is None or job_run.id is None:
            raise ValueError("job_run is required for Stage 1.2 Static classifier")
        return run_static_classifier(phase_result, job_run_id=job_run.id, llm_client=llm_client)

    def run_stage_2_1_workflow_struct(self, job_run: JobRun, phase_result, *, llm_client=None):
        if job_run is None or job_run.id is None:
            raise ValueError("job_run is required for Stage 2.1 Workflow")
        planner = WorkflowStructPlanner(llm_client=llm_client)
        job_meta = JobMeta(
            company_name=job_run.company_name,
            job_title=job_run.job_title,
            industry_context=job_run.industry_context or "",
            business_goal=job_run.business_goal,
        )
        plan = planner.run(job_meta, phase_result.dict())
        try:
            db.apply_workflow_plan(job_run.id, plan)
        except Exception:
            logger.exception("Failed to persist workflow struct plan")
        return plan

    def run_stage_2_2_workflow_mermaid(self, job_run: JobRun, workflow_plan, *, llm_client=None):
        if job_run is None or job_run.id is None:
            raise ValueError("job_run is required for Stage 2.2 Workflow")
        renderer = WorkflowMermaidRenderer(llm_client=llm_client)
        mermaid = renderer.run(workflow_plan)
        return mermaid

    def run_stage_3_workflow(self, *args, **kwargs):  # pragma: no cover - stub
        job_run: JobRun = kwargs.get("job_run")
        ivc_result = kwargs.get("ivc_result")
        if job_run is None or job_run.id is None:
            raise ValueError("job_run is required for Stage 3 Workflow")
        if ivc_result is None:
            raise ValueError("IVC result is required for Stage 3 Workflow")

        job_meta = JobMeta(
            company_name=job_run.company_name,
            job_title=job_run.job_title,
            industry_context=job_run.industry_context or "",
            business_goal=job_run.business_goal,
        )
        return run_workflow(
            job_meta,
            ivc_result.dict(),
            job_run_id=job_run.id,
            llm_client=kwargs.get("llm_client"),
        )

    @staticmethod
    def get_next_label(current: str | None) -> str:
        order = ["0.2", "1.2", "1.3", "2.2"]
        if current is None:
            return order[0]
        if current not in order:
            return order[0]
        idx = order.index(current)
        if idx >= len(order) - 1:
            return order[-1]
        return order[idx + 1]

    def run_pipeline_until_stage(
        self,
        job_run: JobRun,
        target_ui_label: str,
        *,
        manual_jd_text: Optional[str] = None,
        llm_client=None,
    ) -> dict:
        """Execute stages sequentially until target_ui_label."""
        results: dict = {}
        label_to_stage = {s.ui_label: s for s in self.stages}
        target_stage = label_to_stage.get(target_ui_label)
        if target_stage is None:
            raise ValueError(f"Unknown target_ui_label: {target_ui_label}")

        def _should_run(stage: StageMeta) -> bool:
            if stage.ui_group < target_stage.ui_group:
                return True
            if stage.ui_group == target_stage.ui_group and stage.ui_step <= target_stage.ui_step:
                return True
            return False

        # Stage execution
        for stage in self.stages:
            if not stage.implemented or not _should_run(stage):
                continue
            if stage.id == "S0_1_COLLECT":
                collect = self.run_stage_0_1_collect(job_run, manual_jd_text=manual_jd_text)
                results["stage0_collect"] = collect
            elif stage.id == "S0_2_SUMMARIZE":
                summarize = self.run_stage_0_2_summarize(
                    job_run,
                    collect_result=results.get("stage0_collect"),
                    manual_jd_text=manual_jd_text,
                )
                results["stage0_summarize"] = summarize
            elif stage.id == "S1_1_TASK_EXTRACT":
                job_research = results.get("stage0_summarize") or db.get_job_research_result(job_run.id)
                extraction = self.run_stage_1_1_task_extractor(
                    job_run, job_research_result=job_research, llm_client=llm_client
                )
                results["stage1_task_extract"] = extraction
            elif stage.id == "S1_2_PHASE_CLASSIFY":
                job_research = results.get("stage0_summarize") or db.get_job_research_result(job_run.id)
                extraction = results.get("stage1_task_extract")
                phase = self.run_stage_1_2_phase_classifier(
                    job_run,
                    task_extraction_result=extraction,
                    job_research_result=job_research,
                    llm_client=llm_client,
                )
                results["stage1_phase"] = phase
            elif stage.id == "S1_3_STATIC_CLASSIFY":
                phase = results.get("stage1_phase")
                if phase is None:
                    job_research = results.get("stage0_summarize") or db.get_job_research_result(job_run.id)
                    extraction = results.get("stage1_task_extract")
                    phase = self.run_stage_1_2_phase_classifier(
                        job_run,
                        task_extraction_result=extraction,
                        job_research_result=job_research,
                        llm_client=llm_client,
                    )
                    results["stage1_phase"] = phase
                static_result = self.run_stage_1_3_static(job_run=job_run, phase_result=phase, llm_client=llm_client)
                results["stage1_static"] = static_result
            elif stage.id == "S2_1_WORKFLOW_STRUCT":
                phase = results.get("stage1_phase")
                if phase is None:
                    raise ValueError("Phase result missing for Workflow Struct")
                plan = self.run_stage_2_1_workflow_struct(job_run, phase, llm_client=llm_client)
                results["stage2_plan"] = plan
            elif stage.id == "S2_2_WORKFLOW_MERMAID":
                plan = results.get("stage2_plan")
                if plan is None:
                    phase = results.get("stage1_phase")
                    if phase is None:
                        raise ValueError("Workflow plan missing and phase_result unavailable")
                    plan = self.run_stage_2_1_workflow_struct(job_run, phase, llm_client=llm_client)
                    results["stage2_plan"] = plan
                mermaid = self.run_stage_2_2_workflow_mermaid(job_run, plan, llm_client=llm_client)
                results["stage2_mermaid"] = mermaid

        return results
