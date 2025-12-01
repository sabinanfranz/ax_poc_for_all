"""Common JSON schema models for AX Agent Factory IVC stage."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class JobMeta(BaseModel):
    """직무 메타 정보."""

    company_name: str
    job_title: str
    industry_context: str
    business_goal: Optional[str]


class JobInput(BaseModel):
    """IVC 파이프라인 입력: 직무 메타 + 원문 직무 설명."""

    job_meta: JobMeta
    raw_job_desc: str


class IVCAtomicTask(BaseModel):
    """원자 과업(Task Atom) 정의."""

    task_id: str
    task_original_sentence: str
    task_korean: str
    task_english: Optional[str]
    notes: Optional[str]


class TaskExtractionResult(BaseModel):
    """Task Extractor 출력: job_meta 복사 + task_atoms 리스트."""

    job_meta: JobMeta
    task_atoms: List[IVCAtomicTask]


class IVCTaskListInput(BaseModel):
    """Phase Classifier 입력: Task Extractor 결과 그대로 사용."""

    job_meta: JobMeta
    task_atoms: List[IVCAtomicTask]


class IVCTask(BaseModel):
    """Phase Classifier가 분류한 IVC 태스크."""

    task_id: str
    task_korean: str
    task_original_sentence: str
    ivc_phase: str
    ivc_exec_subphase: Optional[str]
    primitive_lv1: str
    classification_reason: str


class PhaseSummary(BaseModel):
    """Phase별 개수 요약."""

    P1_SENSE: dict = Field(default_factory=lambda: {"count": 0})
    P2_DECIDE: dict = Field(default_factory=lambda: {"count": 0})
    P3_EXECUTE_TRANSFORM: dict = Field(default_factory=lambda: {"count": 0})
    P3_EXECUTE_TRANSFER: dict = Field(default_factory=lambda: {"count": 0})
    P3_EXECUTE_COMMIT: dict = Field(default_factory=lambda: {"count": 0})
    P4_ASSURE: dict = Field(default_factory=lambda: {"count": 0})


class PhaseClassificationResult(BaseModel):
    """Phase Classifier 출력: 분류된 태스크 + 요약."""

    job_meta: JobMeta
    ivc_tasks: List[IVCTask]
    phase_summary: PhaseSummary


IVCPipelineOutput = PhaseClassificationResult
