"""Stage metadata definitions for AX Agent Factory pipeline."""

from dataclasses import dataclass
from typing import Literal

StageId = Literal["S0_JOB_RESEARCH", "S1_IVC", "S2_DNA", "S3_WORKFLOW"]


@dataclass
class StageMeta:
    """Metadata describing a pipeline stage for UI and orchestration."""

    id: StageId
    order: int
    label: str
    description: str
    implemented: bool
    run_fn_name: str


PIPELINE_STAGES: list[StageMeta] = [
    StageMeta(
        id="S0_JOB_RESEARCH",
        order=0,
        label="0. Job Research",
        description="회사명 + 직무명을 기반으로 웹 리서치/JD 크롤링 후 raw_job_desc 생성",
        implemented=True,
        run_fn_name="run_stage_0_job_research",
    ),
    StageMeta(
        id="S1_IVC",
        order=1,
        label="1. IVC 분석",
        description="raw_job_desc를 IVC Task 리스트로 구조화",
        implemented=True,
        run_fn_name="run_stage_1_ivc",
    ),
    StageMeta(
        id="S2_DNA",
        order=2,
        label="2. DNA 분류",
        description="Task들에 Primitive/Domain/Mechanism 부여",
        implemented=False,
        run_fn_name="run_stage_2_dna",
    ),
    StageMeta(
        id="S3_WORKFLOW",
        order=3,
        label="3. Workflow Structuring",
        description="Stage/Stream/Task 구조 설계",
        implemented=False,
        run_fn_name="run_stage_3_workflow",
    ),
]
