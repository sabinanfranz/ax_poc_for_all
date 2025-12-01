from datetime import datetime

import pytest

from ax_agent_factory.core import research
from ax_agent_factory.infra import db
from ax_agent_factory.models.job_run import JobRun


class DummyLLM:
    def __init__(self, output: dict) -> None:
        self.output = output
        self.called = False

    def __call__(self, *args, **kwargs):
        self.called = True
        return self.output


def test_run_job_research_saves_to_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    db.set_db_path(str(db_path))

    job_run = db.create_job_run("Acme", "Analyst")
    fake_output = {
        "raw_job_desc": "Test desc",
        "research_sources": [{"url": "http://example.com", "title": "ex", "snippet": "s", "source_type": "jd", "score": 1}],
    }

    monkeypatch.setattr(
        "ax_agent_factory.infra.llm_client.call_gemini_job_research",
        lambda **kwargs: fake_output,
    )

    result = research.run_job_research(job_run)

    assert result.raw_job_desc == "Test desc"
    loaded = db.get_job_research_result(job_run.id)
    assert loaded is not None
    assert loaded.research_sources[0]["url"] == "http://example.com"


def test_run_job_research_requires_id(monkeypatch):
    job_run = JobRun(id=None, company_name="Acme", job_title="Analyst", created_at=datetime.utcnow())
    fake_output = {"raw_job_desc": "", "research_sources": []}
    monkeypatch.setattr(
        "ax_agent_factory.infra.llm_client.call_gemini_job_research",
        lambda **kwargs: fake_output,
    )
    with pytest.raises(ValueError):
        research.run_job_research(job_run)
