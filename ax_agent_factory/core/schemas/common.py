"""Common JSON schema models for AX Agent Factory IVC stage."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

# Compatibility alias for Pydantic v1 to expose model_dump like v2
if not hasattr(BaseModel, "model_dump"):  # type: ignore[attr-defined]
    def _model_dump(self, *args, **kwargs):
        return self.dict(*args, **kwargs)

    BaseModel.model_dump = _model_dump  # type: ignore[attr-defined]


class JobMeta(BaseModel):
    """직무 메타 정보."""

    company_name: str
    job_title: str
    industry_context: Optional[str] = None
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
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


class IVCTaskListInput(BaseModel):
    """Phase Classifier 입력: Task Extractor 결과 그대로 사용."""

    job_meta: JobMeta
    raw_job_desc: str
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
    raw_job_desc: Optional[str] = None
    ivc_tasks: List[IVCTask]
    phase_summary: PhaseSummary
    task_atoms: Optional[List[IVCAtomicTask]] = None
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


class TaskStaticMeta(BaseModel):
    """Static classifier output for a single task."""

    task_id: str
    task_korean: str
    static_type_lv1: str
    static_type_lv2: Optional[str]
    domain_lv1: Optional[str]
    domain_lv2: Optional[str]
    rag_required: bool
    rag_reason: Optional[str]
    value_score: Optional[int]
    complexity_score: Optional[int]
    value_complexity_quadrant: str
    recommended_execution_env: str
    autoability_reason: Optional[str]
    data_entities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class StaticClassificationResult(BaseModel):
    """Static classifier output across tasks."""

    job_meta: JobMeta
    task_static_meta: List[TaskStaticMeta]
    static_summary: dict
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


IVCPipelineOutput = PhaseClassificationResult
