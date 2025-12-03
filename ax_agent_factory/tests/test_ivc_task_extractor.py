import json

import pytest

from ax_agent_factory.core.ivc.task_extractor import IVCTaskExtractor
from ax_agent_factory.core.schemas.common import JobInput
from ax_agent_factory.infra import prompts
from ax_agent_factory.infra.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    """Fake LLM client that returns pre-seeded responses."""

    def __init__(self, responses):
        super().__init__(model_name="fake")
        self._responses = responses
        self._call_count = 0

    def call(self, prompt: str, *, temperature: float = 0.2) -> str:  # type: ignore[override]
        if self._call_count >= len(self._responses):
            raise AssertionError("No more fake responses available.")
        resp = self._responses[self._call_count]
        self._call_count += 1
        return resp


@pytest.fixture
def job_input():
    return JobInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
    )


def _make_payload(job_input: JobInput):
    return {
        "job_meta": job_input.job_meta.model_dump(),
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


@pytest.mark.parametrize(
    "wrapped_output_builder",
    [
        lambda payload: json.dumps(payload, ensure_ascii=False),  # clean JSON
        lambda payload: "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```",  # fenced
        lambda payload: "다음은 결과입니다:\n" + json.dumps(payload, ensure_ascii=False) + "\n감사합니다.",  # with narration
    ],
)
def test_task_extractor_parses_wrapped_json(job_input, wrapped_output_builder, monkeypatch):
    payload = _make_payload(job_input)
    raw_output = wrapped_output_builder(payload)
    monkeypatch.setattr(prompts, "load_prompt", lambda name: "{input_json}")
    extractor = IVCTaskExtractor(llm_client=FakeLLMClient([raw_output]))

    result = extractor.run(job_input)

    assert len(result.task_atoms) == 2
    assert all(atom.task_id.startswith("T0") for atom in result.task_atoms)
    assert all(atom.task_korean.endswith("하기") for atom in result.task_atoms)


def test_task_extractor_records_llm_debug(job_input, monkeypatch):
    payload = _make_payload(job_input)
    raw_output = "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"
    monkeypatch.setattr(prompts, "load_prompt", lambda name: "{input_json}")
    extractor = IVCTaskExtractor(llm_client=FakeLLMClient([raw_output]))

    result = extractor.run(job_input)

    assert result.llm_raw_text == raw_output
    assert result.llm_cleaned_json is not None
    assert result.llm_error is None


def test_task_extractor_sanitizes_trailing_brace(job_input, monkeypatch):
    payload = _make_payload(job_input)
    broken = json.dumps(payload, ensure_ascii=False).replace('"raw_job_desc": "', '"raw_job_desc": "').replace('", "task_atoms"', '"}, "task_atoms"')
    raw_output = f"```json\n{broken}\n```"
    monkeypatch.setattr(prompts, "load_prompt", lambda name: "{input_json}")
    extractor = IVCTaskExtractor(llm_client=FakeLLMClient([raw_output]))

    result = extractor.run(job_input)

    assert len(result.task_atoms) == 2
