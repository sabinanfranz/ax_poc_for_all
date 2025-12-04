"""Orchestrator for IVC Task Extraction and Phase Classification."""

from __future__ import annotations

import logging
from typing import Optional

from ax_agent_factory.core.ivc.phase_classifier import IVCPhaseClassifier
from ax_agent_factory.core.ivc.task_extractor import IVCTaskExtractor
from ax_agent_factory.core.schemas.common import (
    IVCPipelineOutput,
    IVCTaskListInput,
    JobInput,
    TaskExtractionResult,
)
from ax_agent_factory.infra.llm_client import LLMClient
from ax_agent_factory.infra import db

logger = logging.getLogger(__name__)


def run_ivc_pipeline(
    job_input: JobInput,
    *,
    llm_client: Optional[LLMClient] = None,
    job_run_id: Optional[int] = None,
) -> IVCPipelineOutput:
    """
    IVC 파이프라인 실행:
    1) Task Extractor로 원자 과업 추출
    2) Phase Classifier로 Phase/Primitive 분류
    3) 최종 IVCPipelineOutput 반환
    """
    logger.info("IVC pipeline started for job_title=%s", job_input.job_meta.job_title)
    extractor = IVCTaskExtractor(llm_client=llm_client)
    classifier = IVCPhaseClassifier(llm_client=llm_client)

    extraction_result: TaskExtractionResult = extractor.run(job_input, job_run_id=job_run_id)
    if job_run_id is not None:
        try:
            db.save_task_atoms(job_run_id, extraction_result.task_atoms)
        except Exception:
            logger.exception("Failed to persist task_atoms to job_tasks")
    logger.info("IVC TaskExtractor finished. task_atoms=%d", len(extraction_result.task_atoms))
    classifier_input = IVCTaskListInput(
        job_meta=extraction_result.job_meta,
        raw_job_desc=job_input.raw_job_desc,
        task_atoms=extraction_result.task_atoms,
    )
    classification_result = classifier.run(classifier_input, job_run_id=job_run_id)
    if job_run_id is not None:
        try:
            db.apply_ivc_classification(job_run_id, classification_result.ivc_tasks)
        except Exception:
            logger.exception("Failed to persist IVC classification to job_tasks")
    logger.info("IVC PhaseClassifier finished. ivc_tasks=%d", len(classification_result.ivc_tasks))
    # Attach task_atoms to classifier result for UI/cache convenience
    classification_result.task_atoms = extraction_result.task_atoms
    logger.info("IVC pipeline finished.")
    return classification_result
