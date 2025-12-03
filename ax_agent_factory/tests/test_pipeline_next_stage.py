from datetime import datetime

from ax_agent_factory.core.pipeline_manager import PipelineManager
from ax_agent_factory.models.job_run import JobRun


def _job_run_stub() -> JobRun:
    now = datetime.utcnow()
    return JobRun(
        id=1,
        company_name="Acme",
        job_title="Analyst",
        industry_context="",
        business_goal=None,
        manual_jd_text=None,
        status=None,
        created_at=now,
        updated_at=now,
    )


def test_get_next_label():
    assert PipelineManager.get_next_label(None) == "0.2"
    assert PipelineManager.get_next_label("0.2") == "1.2"
    assert PipelineManager.get_next_label("1.2") == "1.3"
    assert PipelineManager.get_next_label("1.3") == "2.2"
    assert PipelineManager.get_next_label("2.2") == "2.2"


def test_run_pipeline_until_stage_order(monkeypatch):
    pm = PipelineManager()
    calls = []

    pm.run_stage_0_1_collect = lambda *args, **kwargs: calls.append("0.1") or "collect"
    pm.run_stage_0_2_summarize = lambda *args, **kwargs: calls.append("0.2") or "summarize"
    pm.run_stage_1_1_task_extractor = lambda *args, **kwargs: calls.append("1.1") or type("Obj", (), {"task_atoms": []})()
    pm.run_stage_1_2_phase_classifier = (
        lambda *args, **kwargs: calls.append("1.2") or type("Obj", (), {"ivc_tasks": [], "task_atoms": [], "phase_summary": type("S", (), {"dict": lambda self: {}})(), "job_meta": type("J", (), {"dict": lambda self: {}})()})()
    )
    pm.run_stage_1_3_static = lambda **kwargs: calls.append("1.3") or type("Obj", (), {"task_static_meta": [], "static_summary": {}})()
    pm.run_stage_2_1_workflow_struct = lambda *args, **kwargs: calls.append("2.1") or type("Plan", (), {"nodes": [], "edges": [], "dict": lambda self: {}})()
    pm.run_stage_2_2_workflow_mermaid = lambda *args, **kwargs: calls.append("2.2") or "mermaid"

    job_run = _job_run_stub()
    results = pm.run_pipeline_until_stage(job_run, "1.3")
    assert results["stage1_static"]
    assert calls == ["0.1", "0.2", "1.1", "1.2", "1.3"]
