from datetime import datetime

from ax_agent_factory.core.ivc.static_classifier import run_static_classifier
from ax_agent_factory.core.schemas.common import IVCAtomicTask, IVCTask, JobMeta, PhaseClassificationResult, PhaseSummary
from ax_agent_factory.infra import db


def test_static_classifier_persists_to_db(tmp_path, monkeypatch):
    db_path = tmp_path / "static.db"
    db.set_db_path(str(db_path))
    job_run = db.create_or_get_job_run("Acme", "Analyst")

    phase_result = PhaseClassificationResult(
        job_meta=JobMeta(company_name="Acme", job_title="Analyst", industry_context="", business_goal=None),
        raw_job_desc="desc",
        ivc_tasks=[
            IVCTask(
                task_id="T01",
                task_korean="데이터 수집하기",
                task_original_sentence="데이터를 수집한다.",
                ivc_phase="P1_SENSE",
                ivc_exec_subphase=None,
                primitive_lv1="SENSE",
                classification_reason="sense",
            )
        ],
        phase_summary=PhaseSummary(P1_SENSE={"count": 1}),
        task_atoms=[
            IVCAtomicTask(
                task_id="T01",
                task_original_sentence="데이터를 수집한다.",
                task_korean="데이터 수집하기",
                task_english=None,
                notes=None,
            )
        ],
    )

    result = run_static_classifier(phase_result, job_run_id=job_run.id, llm_client=None)
    assert result.task_static_meta
    tasks = db.get_job_tasks(job_run.id)
    assert len(tasks) == 1
    assert tasks[0]["static_type_lv1"] is not None
