"""Stage metadata definitions for AX Agent Factory pipeline."""

from dataclasses import dataclass
from typing import Literal

StageId = Literal[
    "S0_1_COLLECT",
    "S0_2_SUMMARIZE",
    "S1_1_TASK_EXTRACT",
    "S1_2_PHASE_CLASSIFY",
    "S1_3_STATIC_CLASSIFY",
    "S2_1_WORKFLOW_STRUCT",
    "S2_2_WORKFLOW_MERMAID",
]


@dataclass
class StageMeta:
    """Metadata describing a pipeline stage for UI and orchestration."""

    id: StageId
    order: int
    label: str
    description: str
    implemented: bool
    run_fn_name: str
    ui_group: int
    ui_step: int
    ui_label: str
    tab_title: str


PIPELINE_STAGES: list[StageMeta] = [
    StageMeta(
        id="S0_1_COLLECT",
        order=0,
        label="0.1 Job Research Collect",
        description="회사명/직무/선택 JD로 웹 리서치 후 raw_sources 수집",
        implemented=True,
        run_fn_name="run_stage_0_1_collect",
        ui_group=0,
        ui_step=1,
        ui_label="0.1",
        tab_title="0.1 Job Research Collect",
    ),
    StageMeta(
        id="S0_2_SUMMARIZE",
        order=1,
        label="0.2 Job Research Summarize",
        description="raw_sources를 통합해 raw_job_desc + research_sources 생성",
        implemented=True,
        run_fn_name="run_stage_0_2_summarize",
        ui_group=0,
        ui_step=2,
        ui_label="0.2",
        tab_title="0.2 Job Research Summarize",
    ),
    StageMeta(
        id="S1_1_TASK_EXTRACT",
        order=2,
        label="1.1 Task Extractor",
        description="raw_job_desc를 원자 과업(task_atoms)으로 분해",
        implemented=True,
        run_fn_name="run_stage_1_1_task_extractor",
        ui_group=1,
        ui_step=1,
        ui_label="1.1",
        tab_title="1.1 Task Extractor",
    ),
    StageMeta(
        id="S1_2_PHASE_CLASSIFY",
        order=3,
        label="1.2 Phase Classifier",
        description="task_atoms를 IVC Phase/Primitive로 분류",
        implemented=True,
        run_fn_name="run_stage_1_2_phase_classifier",
        ui_group=1,
        ui_step=2,
        ui_label="1.2",
        tab_title="1.2 Phase Classifier",
    ),
    StageMeta(
        id="S1_3_STATIC_CLASSIFY",
        order=4,
        label="1.3 Static Task Classifier",
        description="각 Task에 정적 유형/도메인/RAG/가치/복잡도 메타 부여",
        implemented=True,
        run_fn_name="run_stage_1_3_static",
        ui_group=1,
        ui_step=3,
        ui_label="1.3",
        tab_title="1.3 Static Task Classifier",
    ),
    StageMeta(
        id="S2_1_WORKFLOW_STRUCT",
        order=5,
        label="2.1 Workflow Struct",
        description="IVC 결과로 워크플로우 Stage/Stream/Node/Edge 구조화",
        implemented=True,
        run_fn_name="run_stage_2_1_workflow_struct",
        ui_group=2,
        ui_step=1,
        ui_label="2.1",
        tab_title="2.1 Workflow Struct",
    ),
    StageMeta(
        id="S2_2_WORKFLOW_MERMAID",
        order=6,
        label="2.2 Workflow Mermaid",
        description="워크플로우를 Mermaid 코드로 렌더링",
        implemented=True,
        run_fn_name="run_stage_2_2_workflow_mermaid",
        ui_group=2,
        ui_step=2,
        ui_label="2.2",
        tab_title="2.2 Workflow Mermaid",
    ),
]
