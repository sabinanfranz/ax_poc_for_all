"""Orchestrator for IVC Task Extraction and Phase Classification."""

from __future__ import annotations

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


def run_ivc_pipeline(
    job_input: JobInput,
    *,
    llm_client: Optional[LLMClient] = None,
) -> IVCPipelineOutput:
    """
    IVC 파이프라인 실행:
    1) Task Extractor로 원자 과업 추출
    2) Phase Classifier로 Phase/Primitive 분류
    3) 최종 IVCPipelineOutput 반환
    """
    shared_llm = llm_client or LLMClient()
    extractor = IVCTaskExtractor(llm_client=shared_llm)
    classifier = IVCPhaseClassifier(llm_client=shared_llm)

    extraction_result: TaskExtractionResult = extractor.run(job_input)
    classifier_input = IVCTaskListInput(
        job_meta=extraction_result.job_meta, task_atoms=extraction_result.task_atoms
    )
    classification_result = classifier.run(classifier_input)
    return classification_result
