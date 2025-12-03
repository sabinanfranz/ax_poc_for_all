from ax_agent_factory.core.schemas.common import IVCAtomicTask, IVCTask, TaskStaticMeta
from ax_agent_factory.core.schemas.workflow import WorkflowEdge, WorkflowNode, WorkflowPlan, WorkflowStage, WorkflowStream
from ax_agent_factory.infra import db


def test_job_tasks_lifecycle(tmp_path):
    db_path = tmp_path / "tasks.db"
    db.set_db_path(str(db_path))

    job_run = db.create_or_get_job_run("Acme", "Analyst")

    task_atoms = [
        IVCAtomicTask(
            task_id="T01",
            task_original_sentence="데이터를 수집한다.",
            task_korean="데이터 수집하기",
            task_english="collect data",
            notes=None,
        ),
        IVCAtomicTask(
            task_id="T02",
            task_original_sentence="보고서를 작성한다.",
            task_korean="보고서 작성하기",
            task_english="write report",
            notes=None,
        ),
    ]
    db.save_task_atoms(job_run.id, task_atoms)
    rows = db.get_job_tasks(job_run.id)
    assert len(rows) == 2
    assert {r["task_id"] for r in rows} == {"T01", "T02"}

    ivc_tasks = [
        IVCTask(
            task_id="T01",
            task_korean="데이터 수집하기",
            task_original_sentence="데이터를 수집한다.",
            ivc_phase="P1_SENSE",
            ivc_exec_subphase=None,
            primitive_lv1="SENSE",
            classification_reason="sense",
        ),
        IVCTask(
            task_id="T02",
            task_korean="보고서 작성하기",
            task_original_sentence="보고서를 작성한다.",
            ivc_phase="P3_EXECUTE_TRANSFORM",
            ivc_exec_subphase="TRANSFORM",
            primitive_lv1="TRANSFORM",
            classification_reason="execute",
        ),
    ]
    db.apply_ivc_classification(job_run.id, ivc_tasks)

    static_meta = [
        TaskStaticMeta(
            task_id="T01",
            task_korean="데이터 수집하기",
            static_type_lv1="DATA",
            static_type_lv2="COLLECT",
            domain_lv1="ANALYTICS",
            domain_lv2=None,
            rag_required=False,
            rag_reason=None,
            value_score=3,
            complexity_score=2,
            value_complexity_quadrant="MID",
            recommended_execution_env="human_in_loop",
            autoability_reason=None,
            data_entities=["dataset"],
            tags=["analytics"],
        ),
        TaskStaticMeta(
            task_id="T02",
            task_korean="보고서 작성하기",
            static_type_lv1="DOCS",
            static_type_lv2=None,
            domain_lv1=None,
            domain_lv2=None,
            rag_required=True,
            rag_reason="needs corpus",
            value_score=None,
            complexity_score=None,
            value_complexity_quadrant="UNKNOWN",
            recommended_execution_env="human",
            autoability_reason=None,
            data_entities=[],
            tags=[],
        ),
    ]
    db.apply_static_classification(job_run.id, static_meta)

    plan = WorkflowPlan(
        workflow_name="Test",
        stages=[WorkflowStage(stage_id="S1", name="Stage 1")],
        streams=[WorkflowStream(stream_id="S1_ST1", name="Main", stage_id="S1")],
        nodes=[
            WorkflowNode(node_id="T01", label="데이터 수집하기", stage_id="S1", stream_id="S1_ST1", is_entry=True),
            WorkflowNode(node_id="T02", label="보고서 작성하기", stage_id="S1", stream_id="S1_ST1", is_exit=True),
        ],
        edges=[WorkflowEdge(source="T01", target="T02")],
        entry_points=["T01"],
        exit_points=["T02"],
    )
    db.apply_workflow_plan(job_run.id, plan)

    rows_after = db.get_job_tasks(job_run.id)
    assert any(r["ivc_phase"] == "P1_SENSE" for r in rows_after)
    assert any(r["stage_id"] == "S1" for r in rows_after)
    assert any(r["is_entry"] == 1 for r in rows_after)

    edges = db.get_job_task_edges(job_run.id)
    assert len(edges) == 1
    assert edges[0]["source_task_id"] == "T01"
