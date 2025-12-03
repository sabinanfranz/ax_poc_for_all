import json
from types import SimpleNamespace

from ax_agent_factory.infra import db, llm_client


def _mock_gemini(monkeypatch, response):
    """Patch llm_client.genai/types so helpers use a fake Gemini response."""

    class FakeModels:
        def generate_content(self, *args, **kwargs):
            return response

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(llm_client, "genai", SimpleNamespace(Client=FakeClient))
    monkeypatch.setattr(llm_client, "types", SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs))


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
    assert log.tokens_prompt is None
    assert log.tokens_completion is None
    assert log.tokens_total is None


def test_llm_call_log_records_tokens_when_usage_present(tmp_path, monkeypatch):
    db_path = tmp_path / "test_usage.db"
    db.set_db_path(str(db_path))
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    job_input = {
        "job_meta": {"company_name": "Acme", "job_title": "Engineer"},
        "raw_job_desc": "설명",
    }
    payload = {
        "job_meta": job_input["job_meta"],
        "task_atoms": [
            {
                "task_id": "T01",
                "task_original_sentence": "테스트",
                "task_korean": "테스트하기",
                "task_english": "test",
                "notes": None,
            }
        ],
    }
    usage_metadata = SimpleNamespace(prompt_token_count=10, candidates_token_count=20, total_token_count=30)
    response = SimpleNamespace(text=json.dumps(payload, ensure_ascii=False), usage_metadata=usage_metadata)
    _mock_gemini(monkeypatch, response)

    llm_client.call_task_extractor(job_input, job_run_id=5, model="usage-model")

    logs = db.get_llm_calls_by_job_run(5)
    assert len(logs) == 1
    log = logs[0]
    assert log.tokens_prompt == 10
    assert log.tokens_completion == 20
    assert log.tokens_total == 30


def test_llm_call_log_tokens_none_when_usage_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "test_usage_missing.db"
    db.set_db_path(str(db_path))
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    job_input = {
        "job_meta": {"company_name": "Beta", "job_title": "Designer"},
        "raw_job_desc": "설명",
    }
    payload = {
        "job_meta": job_input["job_meta"],
        "task_atoms": [
            {
                "task_id": "T01",
                "task_original_sentence": "테스트",
                "task_korean": "테스트하기",
                "task_english": "test",
                "notes": None,
            }
        ],
    }
    response = SimpleNamespace(text=json.dumps(payload, ensure_ascii=False), usage_metadata=None)
    _mock_gemini(monkeypatch, response)

    llm_client.call_task_extractor(job_input, job_run_id=9, model="usage-missing-model")

    logs = db.get_llm_calls_by_job_run(9)
    assert len(logs) == 1
    log = logs[0]
    assert log.tokens_prompt is None
    assert log.tokens_completion is None
    assert log.tokens_total is None
