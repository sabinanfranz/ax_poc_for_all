import json

from ax_agent_factory.core.ivc.phase_classifier import IVCPhaseClassifier
from ax_agent_factory.core.schemas.common import IVCAtomicTask, IVCTaskListInput
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


def test_phase_classifier_assigns_expected_phases():
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
            task_english="create report",
            notes=None,
        ),
    ]
    task_list_input = IVCTaskListInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
        task_atoms=task_atoms,
    )

    classifier_output = {
        "job_meta": task_list_input.job_meta.model_dump(),
        "raw_job_desc": task_list_input.raw_job_desc,
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
                "ivc_phase": "P3_EXECUTE_TRANSFORM",
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
        "task_atoms": [atom.model_dump() for atom in task_atoms],
    }

    raw_output = json.dumps(classifier_output, ensure_ascii=False)
    classifier = IVCPhaseClassifier(llm_client=FakeLLMClient([raw_output]))

    result = classifier.run(task_list_input)

    assert len(result.ivc_tasks) == 2
    assert result.ivc_tasks[0].ivc_phase == "P1_SENSE"
    assert result.ivc_tasks[1].ivc_exec_subphase == "TRANSFORM"
    assert result.phase_summary.P3_EXECUTE_TRANSFORM["count"] == 1
    assert result.raw_job_desc == task_list_input.raw_job_desc


def test_phase_classifier_records_llm_debug():
    task_atoms = [
        IVCAtomicTask(
            task_id="T01",
            task_original_sentence="데이터를 수집한다.",
            task_korean="데이터 수집하기",
            task_english="collect data",
            notes=None,
        )
    ]
    task_list_input = IVCTaskListInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
        task_atoms=task_atoms,
    )
    classifier_output = {
        "job_meta": task_list_input.job_meta.model_dump(),
        "raw_job_desc": task_list_input.raw_job_desc,
        "ivc_tasks": [
            {
                "task_id": "T01",
                "task_korean": "데이터 수집하기",
                "task_original_sentence": "데이터를 수집한다.",
                "ivc_phase": "P1_SENSE",
                "ivc_exec_subphase": None,
                "primitive_lv1": "SENSE",
                "classification_reason": "원시 데이터 기록 확보",
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
        "task_atoms": [atom.model_dump() for atom in task_atoms],
    }
    raw_output = json.dumps(classifier_output, ensure_ascii=False)
    classifier = IVCPhaseClassifier(llm_client=FakeLLMClient([raw_output]))

    result = classifier.run(task_list_input)

    assert result.llm_raw_text == raw_output
    assert result.llm_cleaned_json is not None
    assert result.llm_error is None


def test_phase_classifier_sanitizes_trailing_brace():
    task_atoms = [
        IVCAtomicTask(
            task_id="T01",
            task_original_sentence="데이터를 수집한다.",
            task_korean="데이터 수집하기",
            task_english="collect data",
            notes=None,
        )
    ]
    task_list_input = IVCTaskListInput(
        job_meta={
            "company_name": "Acme",
            "job_title": "Data Analyst",
            "industry_context": "Tech",
            "business_goal": None,
        },
        raw_job_desc="데이터를 수집하고 보고서를 작성한다.",
        task_atoms=task_atoms,
    )
    payload = {
        "job_meta": task_list_input.job_meta.model_dump(),
        "raw_job_desc": task_list_input.raw_job_desc,
        "ivc_tasks": [
            {
                "task_id": "T01",
                "task_korean": "데이터 수집하기",
                "task_original_sentence": "데이터를 수집한다.",
                "ivc_phase": "P1_SENSE",
                "ivc_exec_subphase": None,
                "primitive_lv1": "SENSE",
                "classification_reason": "원시 데이터 기록 확보",
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
        "task_atoms": [atom.model_dump() for atom in task_atoms],
    }
    broken = json.dumps(payload, ensure_ascii=False).replace('"raw_job_desc": "', '"raw_job_desc": "').replace('", "ivc_tasks"', '"}, "ivc_tasks"')
    raw_output = f"```json\n{broken}\n```"
    classifier = IVCPhaseClassifier(llm_client=FakeLLMClient([raw_output]))

    result = classifier.run(task_list_input)

    assert result.ivc_tasks[0].ivc_phase == "P1_SENSE"
