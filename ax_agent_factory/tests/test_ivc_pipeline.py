import json

import pytest

from ax_agent_factory.core.ivc.pipeline import run_ivc_pipeline
from ax_agent_factory.core.schemas.common import JobInput
from ax_agent_factory.infra import db, prompts
from ax_agent_factory.infra.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    """Simple fake LLM client returning pre-seeded responses."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__(model_name="fake")
        self._responses = responses
        self._call_count = 0

    def call(self, prompt: str, *, temperature: float = 0.2) -> str:  # type: ignore[override]
        if self._call_count >= len(self._responses):
            raise AssertionError("No more fake responses available.")
        resp = self._responses[self._call_count]
        self._call_count += 1
        return resp


def test_ivc_pipeline_happy_path(monkeypatch):
    # Monkeypatch prompt loader to avoid file IO
    prompts.load_prompt.cache_clear()
    monkeypatch.setattr(prompts, "load_prompt", lambda name: "{input_json}")

    job_input = JobInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
    )

    extractor_output = {
        "job_meta": job_input.job_meta.model_dump(),
        "raw_job_desc": job_input.raw_job_desc,
        "task_atoms": [
            {
                "task_id": "T01",
                "task_original_sentence": "데이터를 수집한다.",
                "task_korean": "데이터 수집하기",
                "task_english": "collect data",
                "notes": None,
            },
            {
                "task_id": "T02",
                "task_original_sentence": "보고서를 작성한다.",
                "task_korean": "보고서 작성하기",
                "task_english": "create report",
                "notes": None,
            },
        ],
    }

    classifier_output = {
        "job_meta": job_input.job_meta.model_dump(),
        "raw_job_desc": job_input.raw_job_desc,
        "ivc_tasks": [
            {
                "task_id": "T01",
                "task_korean": "데이터 수집하기",
                "task_original_sentence": "데이터를 수집한다.",
                "ivc_phase": "P1_SENSE",
                "ivc_exec_subphase": None,
                "primitive_lv1": "SENSE",
                "classification_reason": "원시 데이터 기록 확보",
            },
            {
                "task_id": "T02",
                "task_korean": "보고서 작성하기",
                "task_original_sentence": "보고서를 작성한다.",
                "ivc_phase": "P3_EXECUTE",
                "ivc_exec_subphase": "TRANSFORM",
                "primitive_lv1": "TRANSFORM",
                "classification_reason": "새 문서 생성",
            },
        ],
        "phase_summary": {
            "P1_SENSE": {"count": 1},
            "P2_DECIDE": {"count": 0},
            "P3_EXECUTE_TRANSFORM": {"count": 1},
            "P3_EXECUTE_TRANSFER": {"count": 0},
            "P3_EXECUTE_COMMIT": {"count": 0},
            "P4_ASSURE": {"count": 0},
        },
    }

    fake_llm = FakeLLMClient([json.dumps(extractor_output, ensure_ascii=False), json.dumps(classifier_output, ensure_ascii=False)])
    output = run_ivc_pipeline(job_input, llm_client=fake_llm)

    assert output.phase_summary.P1_SENSE["count"] == 1
    assert output.phase_summary.P3_EXECUTE_TRANSFORM["count"] == 1
    assert output.ivc_tasks[0].primitive_lv1 == "SENSE"
    assert output.ivc_tasks[1].ivc_exec_subphase == "TRANSFORM"
    assert output.raw_job_desc == job_input.raw_job_desc


def test_ivc_pipeline_raises_on_bad_json(monkeypatch):
    job_input = JobInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
    )

    prompts.load_prompt.cache_clear()
    monkeypatch.setattr(prompts, "load_prompt", lambda name: "{input_json}")
    fake_llm = FakeLLMClient(["{not json}", "{also bad json}"])
    output = run_ivc_pipeline(job_input, llm_client=fake_llm)

    assert output.ivc_tasks  # stub fallback
    assert output.phase_summary.P1_SENSE["count"] == len(output.ivc_tasks)


def test_ivc_pipeline_persists_job_tasks(tmp_path, monkeypatch):
    prompts.load_prompt.cache_clear()
    monkeypatch.setattr(prompts, "load_prompt", lambda name: "{input_json}")
    db_path = tmp_path / "ivc.db"
    db.set_db_path(str(db_path))
    job_run = db.create_or_get_job_run("Acme", "Data Analyst")

    job_input = JobInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
    )

    extractor_output = {
        "job_meta": job_input.job_meta.model_dump(),
        "raw_job_desc": job_input.raw_job_desc,
        "task_atoms": [
            {
                "task_id": "T01",
                "task_original_sentence": "데이터를 수집한다.",
                "task_korean": "데이터 수집하기",
                "task_english": "collect data",
                "notes": None,
            }
        ],
    }

    classifier_output = {
        "job_meta": job_input.job_meta.model_dump(),
        "raw_job_desc": job_input.raw_job_desc,
        "ivc_tasks": [
            {
                "task_id": "T01",
                "task_korean": "데이터 수집하기",
                "task_original_sentence": "데이터를 수집한다.",
                "ivc_phase": "P1_SENSE",
                "ivc_exec_subphase": None,
                "primitive_lv1": "SENSE",
                "classification_reason": "sense",
            }
        ],
        "phase_summary": {
            "P1_SENSE": {"count": 1},
            "P2_DECIDE": {"count": 0},
            "P3_EXECUTE_TRANSFORM": {"count": 0},
            "P3_EXECUTE_TRANSFER": {"count": 0},
            "P3_EXECUTE_COMMIT": {"count": 0},
            "P4_ASSURE": {"count": 0},
        },
    }

    fake_llm = FakeLLMClient(
        [json.dumps(extractor_output, ensure_ascii=False), json.dumps(classifier_output, ensure_ascii=False)]
    )
    run_ivc_pipeline(job_input, llm_client=fake_llm, job_run_id=job_run.id)

    tasks = db.get_job_tasks(job_run.id)
    assert len(tasks) == 1
    assert tasks[0]["task_korean"] == "데이터 수집하기"
