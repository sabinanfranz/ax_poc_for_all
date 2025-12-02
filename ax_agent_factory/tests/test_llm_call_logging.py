import json

from ax_agent_factory.infra import db, llm_client


def test_llm_call_log_saved_on_collect_stub(tmp_path):
    db_path = tmp_path / "test.db"
    db.set_db_path(str(db_path))

    # Without GOOGLE_API_KEY / genai, collect returns stub but should log
    result = llm_client.call_job_research_collect(
        company_name="Acme",
        job_title="Analyst",
        manual_jd_text=None,
        job_run_id=1,
        model="test-model",
    )

    assert "raw_sources" in result

    logs = db.get_llm_calls_by_job_run(1)
    assert len(logs) == 1
    log = logs[0]
    assert log.stage_name == "stage0_collect"
    assert log.model_name == "test-model"
    assert log.status in ("stub_fallback", "success", "json_parse_error")
    assert json.loads(log.input_payload_json)["job_title"] == "Analyst"
