"""Static task classifier (Stage 1.2) that enriches tasks with domain/static labels."""

from __future__ import annotations

import logging
from typing import Optional

from ax_agent_factory.core.schemas.common import (
    PhaseClassificationResult,
    StaticClassificationResult,
    TaskStaticMeta,
)
from ax_agent_factory.infra import db
from ax_agent_factory.infra.llm_client import (
    LLMClient,
    InvalidLLMJsonError,
    call_static_task_classifier,
)

logger = logging.getLogger(__name__)


class StaticTaskClassifier:
    """Stage 1.2: static typing/classification of tasks."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client

    def run(
        self,
        phase_result: PhaseClassificationResult,
        *,
        job_run_id: Optional[int] = None,
    ) -> StaticClassificationResult:
        payload = {
            "job_meta": phase_result.job_meta.model_dump(),
            "task_atoms": [atom.model_dump() for atom in phase_result.task_atoms or []],
            "ivc_tasks": [task.model_dump() for task in phase_result.ivc_tasks],
            "phase_summary": phase_result.phase_summary.model_dump(),
        }
        logger.info("Static classifier started for job_title=%s", phase_result.job_meta.job_title)
        try:
            llm_output = call_static_task_classifier(
                payload,
                job_run_id=job_run_id,
                llm_client_override=self.llm,
            )
            result = StaticClassificationResult(**llm_output)
            if hasattr(result, "llm_raw_text"):
                result.llm_raw_text = llm_output.get("_raw_text")  # type: ignore[attr-defined]
                result.llm_cleaned_json = llm_output.get("_cleaned_json")  # type: ignore[attr-defined]
                result.llm_error = llm_output.get("llm_error")  # type: ignore[attr-defined]
            if job_run_id is not None:
                try:
                    db.apply_static_classification(job_run_id, result.task_static_meta)
                except Exception:
                    logger.exception("Failed to persist static classification to job_tasks")
            return result
        except InvalidLLMJsonError:
            logger.warning("Static classifier JSON parse failed; returning stub", exc_info=False)
            result = self._stub_result(phase_result)
        except Exception:
            logger.error("Static classifier unexpected error", exc_info=True)
            raise
        if job_run_id is not None:
            try:
                db.apply_static_classification(job_run_id, result.task_static_meta)
            except Exception:
                logger.exception("Failed to persist static classification to job_tasks")
        return result

    def _stub_result(self, phase_result: PhaseClassificationResult) -> StaticClassificationResult:
        """Generate simple deterministic static meta when LLM unavailable."""
        task_static_meta: list[TaskStaticMeta] = []
        for task in phase_result.ivc_tasks:
            task_static_meta.append(
                TaskStaticMeta(
                    task_id=task.task_id,
                    task_korean=task.task_korean,
                    static_type_lv1="GENERAL",
                    static_type_lv2=None,
                    domain_lv1=None,
                    domain_lv2=None,
                    rag_required=False,
                    rag_reason=None,
                    value_score=None,
                    complexity_score=None,
                    value_complexity_quadrant="UNKNOWN",
                    recommended_execution_env="human_in_loop",
                    autoability_reason=None,
                    data_entities=[],
                    tags=[],
                )
            )
        return StaticClassificationResult(
            job_meta=phase_result.job_meta,
            task_static_meta=task_static_meta,
            static_summary={},
        )


def run_static_classifier(
    phase_result: PhaseClassificationResult,
    *,
    job_run_id: Optional[int] = None,
    llm_client: Optional[LLMClient] = None,
) -> StaticClassificationResult:
    classifier = StaticTaskClassifier(llm_client=llm_client)
    return classifier.run(phase_result, job_run_id=job_run_id)
