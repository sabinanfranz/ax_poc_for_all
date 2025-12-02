"""IVC Phase Classifier module (Stage 1.1)."""

from __future__ import annotations

import json
import logging
from typing import Optional

from ax_agent_factory.core.schemas.common import IVCAtomicTask, IVCTaskListInput, PhaseClassificationResult
from ax_agent_factory.infra.llm_client import (
    LLMClient,
    InvalidLLMJsonError,
    _extract_json_from_text,
)
from ax_agent_factory.infra.prompts import load_prompt

logger = logging.getLogger(__name__)


class IVCPhaseClassifier:
    """IVC-B Phase Classifier: Task Atom을 IVC Phase/Primitive로 분류."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient()

    def build_prompt(self, task_list_input: IVCTaskListInput) -> str:
        """[IVC_PHASE_CLASSIFIER_PROMPT_SPEC]에 따른 프롬프트 생성."""
        input_json = task_list_input.model_dump()
        template = load_prompt("ivc_phase_classifier")
        return template.replace("{input_json}", json.dumps(input_json, ensure_ascii=False))

    def parse_response(self, raw_output: str) -> PhaseClassificationResult:
        """LLM 응답(JSON 문자열 기대)을 파싱해 PhaseClassificationResult로 변환."""
        logger.info("Parsing LLM JSON for ivc_phase_classifier...")
        json_text = _extract_json_from_text(raw_output)
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            logger.error("Phase Classifier JSON decoding failed", exc_info=True)
            raise InvalidLLMJsonError(
                "Failed to parse Phase Classifier output as JSON",
                raw_text=raw_output,
                json_text=json_text,
            ) from exc

        if not isinstance(data, dict):
            raise InvalidLLMJsonError(
                "Phase Classifier JSON is not an object",
                raw_text=raw_output,
                json_text=json_text,
            )
        try:
            result = parse_phase_classification_dict(data)
            logger.info("Phase Classifier parsing succeeded. ivc_task_count=%d", len(result.ivc_tasks))
            return result
        except Exception:
            logger.error("Phase Classifier payload validation failed", exc_info=True)
            raise

    def run(self, task_list_input: IVCTaskListInput) -> PhaseClassificationResult:
        """프롬프트 생성 → LLM 호출 → 파싱."""
        logger.info(
            "IVC PhaseClassifier started for job_title=%s, company_name=%s",
            task_list_input.job_meta.job_title,
            task_list_input.job_meta.company_name,
        )
        prompt = self.build_prompt(task_list_input)
        try:
            logger.info("Calling ivc_phase_classifier LLM...")
            raw_output = self.llm.call(prompt)
            logger.info(
                "LLM response received. length=%d, first_200_chars=%s",
                len(raw_output or ""),
                (raw_output or "")[:200],
            )
            return self.parse_response(raw_output)
        except InvalidLLMJsonError:
            logger.error("Phase Classifier JSON parsing error", exc_info=True)
            raise
        except NotImplementedError:
            return self._stub_result(task_list_input)

    def _stub_result(self, task_list_input: IVCTaskListInput) -> PhaseClassificationResult:
        """Stub classification assigning SENSE to all tasks when LLM is unavailable."""
        ivc_tasks = []
        summary_counts = {
            "P1_SENSE": 0,
            "P2_DECIDE": 0,
            "P3_EXECUTE_TRANSFORM": 0,
            "P3_EXECUTE_TRANSFER": 0,
            "P3_EXECUTE_COMMIT": 0,
            "P4_ASSURE": 0,
        }
        for atom in task_list_input.task_atoms:
            ivc_tasks.append(
                {
                    "task_id": atom.task_id,
                    "task_korean": atom.task_korean,
                    "task_original_sentence": atom.task_original_sentence,
                    "ivc_phase": "P1_SENSE",
                    "ivc_exec_subphase": None,
                    "primitive_lv1": "SENSE",
                    "classification_reason": "Stub: default to SENSE",
                }
            )
            summary_counts["P1_SENSE"] += 1

        phase_summary = {
            "P1_SENSE": {"count": summary_counts["P1_SENSE"]},
            "P2_DECIDE": {"count": summary_counts["P2_DECIDE"]},
            "P3_EXECUTE_TRANSFORM": {"count": summary_counts["P3_EXECUTE_TRANSFORM"]},
            "P3_EXECUTE_TRANSFER": {"count": summary_counts["P3_EXECUTE_TRANSFER"]},
            "P3_EXECUTE_COMMIT": {"count": summary_counts["P3_EXECUTE_COMMIT"]},
            "P4_ASSURE": {"count": summary_counts["P4_ASSURE"]},
        }
        stub_payload = {
            "job_meta": task_list_input.job_meta.dict(),
            "raw_job_desc": task_list_input.raw_job_desc,
            "ivc_tasks": ivc_tasks,
            "phase_summary": phase_summary,
            "task_atoms": [atom.dict() for atom in task_list_input.task_atoms],
        }
        return PhaseClassificationResult(**stub_payload)


def parse_phase_classification_dict(payload: dict) -> PhaseClassificationResult:
    """Pure conversion helper for validation/testing."""
    return PhaseClassificationResult(**payload)
