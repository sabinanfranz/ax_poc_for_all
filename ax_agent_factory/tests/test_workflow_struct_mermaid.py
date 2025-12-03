import json

from ax_agent_factory.core.schemas.common import JobMeta
from ax_agent_factory.core.workflow import WorkflowMermaidRenderer, WorkflowStructPlanner
from ax_agent_factory.infra import db
from ax_agent_factory.infra.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    """Fake LLM client returning pre-seeded responses."""

    def __init__(self, responses):
        super().__init__(model_name="fake")
        self._responses = responses
        self._idx = 0

    def call(self, prompt: str, *, temperature: float = 0.2):  # type: ignore[override]
        if self._idx >= len(self._responses):
            raise AssertionError("No more fake responses")
        resp = self._responses[self._idx]
        self._idx += 1
        return resp


def test_workflow_struct_and_mermaid_with_clean_json():
    job_meta = JobMeta(company_name="Acme", job_title="Data Analyst", industry_context="Tech", business_goal=None)
    struct_payload = {
        "workflow_name": "Data Analyst Workflow",
        "workflow_summary": "summary",
        "stages": [{"stage_id": "S1", "name": "Stage 1"}],
        "streams": [{"stream_id": "S1_ST1", "name": "Main", "stage_id": "S1"}],
        "nodes": [
            {"node_id": "T1", "label": "시작", "stage_id": "S1", "stream_id": "S1_ST1", "is_entry": True},
            {"node_id": "T2", "label": "종료", "stage_id": "S1", "stream_id": "S1_ST1", "is_exit": True},
        ],
        "edges": [{"source": "T1", "target": "T2"}],
        "entry_points": ["T1"],
        "exit_points": ["T2"],
    }
    mermaid_payload = {
        "workflow_name": "Data Analyst Workflow",
        "mermaid_code": "flowchart TD\n T1-->T2",
        "warnings": [],
    }

    fake_llm = FakeLLMClient([
        json.dumps(struct_payload, ensure_ascii=False),
        json.dumps(mermaid_payload, ensure_ascii=False),
    ])

    planner = WorkflowStructPlanner(llm_client=fake_llm)
    renderer = WorkflowMermaidRenderer(llm_client=fake_llm)

    plan = planner.run(job_meta, {"ivc_tasks": [], "task_atoms": []})
    diagram = renderer.run(plan)

    assert plan.workflow_name == "Data Analyst Workflow"
    assert diagram.mermaid_code.startswith("flowchart TD")


def test_workflow_struct_stub_on_bad_json():
    job_meta = JobMeta(company_name="Acme", job_title="Data Analyst", industry_context="Tech", business_goal=None)
    fake_llm = FakeLLMClient(["{not json}", "{not json either}"])
    planner = WorkflowStructPlanner(llm_client=fake_llm)
    plan = planner.run(job_meta, {"ivc_tasks": [], "task_atoms": []})

    assert plan.nodes  # stub fallback
    assert plan.entry_points


def test_apply_workflow_plan_persists(tmp_path):
    db_path = tmp_path / "workflow.db"
    db.set_db_path(str(db_path))
    job_run = db.create_or_get_job_run("Acme", "Data Analyst")
    job_meta = JobMeta(company_name="Acme", job_title="Data Analyst", industry_context="Tech", business_goal=None)
    struct_payload = {
        "workflow_name": "Data Analyst Workflow",
        "stages": [{"stage_id": "S1", "name": "Stage 1"}],
        "streams": [{"stream_id": "S1_ST1", "name": "Main", "stage_id": "S1"}],
        "nodes": [
            {"node_id": "T1", "label": "시작", "stage_id": "S1", "stream_id": "S1_ST1", "is_entry": True},
            {"node_id": "T2", "label": "종료", "stage_id": "S1", "stream_id": "S1_ST1", "is_exit": True},
        ],
        "edges": [{"source": "T1", "target": "T2"}],
        "entry_points": ["T1"],
        "exit_points": ["T2"],
    }
    plan = WorkflowStructPlanner(llm_client=None)
    workflow_plan = plan.run(job_meta, {"ivc_tasks": [], "task_atoms": []})
    # override with deterministic payload for persistence
    workflow_plan = workflow_plan.copy(update=struct_payload)

    db.apply_workflow_plan(job_run.id, workflow_plan)
    tasks = db.get_job_tasks(job_run.id)
    assert len(tasks) == 2
    assert any(row["is_entry"] == 1 for row in tasks)
    edges = db.get_job_task_edges(job_run.id)
    assert len(edges) == 1
