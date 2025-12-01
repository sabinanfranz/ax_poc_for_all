import pytest

from ax_agent_factory.core.pipeline_manager import PipelineManager
from ax_agent_factory.infra import db
from ax_agent_factory.models.job_run import JobResearchResult


def test_pipeline_manager_cache(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    db.set_db_path(str(db_path))
    manager = PipelineManager()
    job_run = manager.create_or_get_job_run("Acme", "Analyst")

    fake_output = JobResearchResult(job_run_id=job_run.id, raw_job_desc="Test desc", research_sources=[])

    call_count = {"n": 0}

    def fake_run_job_research(job_run, manual_jd_text=None):
        call_count["n"] += 1
        # mimic real behavior: save to DB for caching
        db.save_job_research_result(fake_output)
        return fake_output

    monkeypatch.setattr("ax_agent_factory.core.pipeline_manager.research.run_job_research", fake_run_job_research)

    result1 = manager.run_stage_0_job_research(job_run, force_rerun=True)
    assert result1.raw_job_desc == "Test desc"
    assert call_count["n"] == 1

    result2 = manager.run_stage_0_job_research(job_run, force_rerun=False)
    assert result2.raw_job_desc == "Test desc"
    assert call_count["n"] == 1


def test_stage_stub_raises():
    manager = PipelineManager()
    with pytest.raises(ValueError):
        manager.run_stage_1_ivc()


def test_run_stage_1_ivc_with_cached_stage0(tmp_path, monkeypatch):
    from ax_agent_factory.core.schemas.common import PhaseClassificationResult, PhaseSummary

    db_path = tmp_path / "test.db"
    db.set_db_path(str(db_path))
    manager = PipelineManager()
    job_run = manager.create_or_get_job_run("Acme", "Analyst")

    # Seed stage0 result in DB
    db.save_job_research_result(JobResearchResult(job_run_id=job_run.id, raw_job_desc="desc", research_sources=[]))

    fake_phase = PhaseClassificationResult(
        job_meta={
            "company_name": job_run.company_name,
            "job_title": job_run.job_title,
            "industry_context": "",
            "business_goal": None,
        },
        ivc_tasks=[],
        phase_summary=PhaseSummary(),
    )

    monkeypatch.setattr("ax_agent_factory.core.pipeline_manager.run_ivc_pipeline", lambda *args, **kwargs: fake_phase)

    output = manager.run_stage_1_ivc(job_run=job_run)
    assert output.job_meta.company_name == job_run.company_name
