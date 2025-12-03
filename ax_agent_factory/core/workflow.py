"""Stage 2 Workflow (2.1 구조화 → 2.2 Mermaid 렌더링)."""

from __future__ import annotations

import logging
from typing import Optional

from ax_agent_factory.core.schemas.common import JobMeta
from ax_agent_factory.core.schemas.workflow import MermaidDiagram, WorkflowPlan
from ax_agent_factory.infra import db
from ax_agent_factory.infra.llm_client import (
    InvalidLLMJsonError,
    call_workflow_mermaid,
    call_workflow_struct,
    _stub_workflow_mermaid,
    _stub_workflow_struct,
)

logger = logging.getLogger(__name__)


class WorkflowStructPlanner:
    """Stage 2.1: Task 리스트로 워크플로우 구조를 설계."""

    def __init__(self, llm_client=None) -> None:
        self.llm = llm_client

    def run(self, job_meta: JobMeta, ivc_payload: dict) -> WorkflowPlan:
        """job_meta + ivc_tasks/task_atoms로 워크플로우 구조화."""
        logger.info("Workflow Struct planner started for job_title=%s", job_meta.job_title)
        payload = {
            "job_meta": job_meta.model_dump(),
            "raw_job_desc": ivc_payload.get("raw_job_desc"),
            "task_atoms": ivc_payload.get("task_atoms"),
            "ivc_tasks": ivc_payload.get("ivc_tasks"),
            "phase_summary": ivc_payload.get("phase_summary"),
        }
        try:
            llm_output = call_workflow_struct(payload, llm_client_override=self.llm)
            result = WorkflowPlan(**llm_output)
            if hasattr(result, "llm_raw_text"):
                result.llm_raw_text = llm_output.get("_raw_text")  # type: ignore[attr-defined]
                result.llm_cleaned_json = llm_output.get("_cleaned_json")  # type: ignore[attr-defined]
                result.llm_error = llm_output.get("llm_error")  # type: ignore[attr-defined]
            logger.info("Workflow Struct succeeded. nodes=%d edges=%d", len(result.nodes), len(result.edges))
            return result
        except InvalidLLMJsonError as exc:
            logger.error("Workflow Struct JSON parsing error", exc_info=True)
            stub = _stub_workflow_struct(payload, llm_error=str(exc))
            return WorkflowPlan(**stub)
        except Exception:
            logger.error("Workflow Struct unexpected error", exc_info=True)
            raise


class WorkflowMermaidRenderer:
    """Stage 2.2: 워크플로우 구조를 Mermaid 코드로 렌더."""

    def __init__(self, llm_client=None) -> None:
        self.llm = llm_client

    def run(self, workflow_plan: WorkflowPlan) -> MermaidDiagram:
        logger.info("Workflow Mermaid rendering started for workflow=%s", workflow_plan.workflow_name)
        try:
            llm_output = call_workflow_mermaid(workflow_plan.model_dump(), llm_client_override=self.llm)
            result = MermaidDiagram(**llm_output)
            if hasattr(result, "llm_raw_text"):
                result.llm_raw_text = llm_output.get("_raw_text")  # type: ignore[attr-defined]
                result.llm_cleaned_json = llm_output.get("_cleaned_json")  # type: ignore[attr-defined]
                result.llm_error = llm_output.get("llm_error")  # type: ignore[attr-defined]
            logger.info("Workflow Mermaid rendering succeeded. code_length=%d", len(result.mermaid_code))
            return result
        except InvalidLLMJsonError as exc:
            logger.error("Workflow Mermaid JSON parsing error", exc_info=True)
            stub = _stub_workflow_mermaid(workflow_plan.model_dump(), llm_error=str(exc))
            return MermaidDiagram(**stub)
        except Exception:
            logger.error("Workflow Mermaid unexpected error", exc_info=True)
            raise


def run_workflow(
    job_meta: JobMeta,
    ivc_payload: dict,
    *,
    job_run_id: Optional[int] = None,
    llm_client=None,
) -> tuple[WorkflowPlan, MermaidDiagram]:
    """Stage 2 파이프라인: 2.1 구조화 → 2.2 머메이드."""
    planner = WorkflowStructPlanner(llm_client=llm_client)
    renderer = WorkflowMermaidRenderer(llm_client=llm_client)

    plan = planner.run(job_meta, ivc_payload)
    if job_run_id is not None:
        try:
            db.apply_workflow_plan(job_run_id, plan)
        except Exception:
            logger.exception("Failed to persist workflow plan to job_tasks/job_task_edges")
    mermaid = renderer.run(plan)
    return plan, mermaid
