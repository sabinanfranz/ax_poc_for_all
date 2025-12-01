"""IVC Task Extractor module (Stage 1.1)."""

from __future__ import annotations

import json
import logging
from typing import Optional

from ax_agent_factory.core.schemas.common import IVCAtomicTask, JobInput, TaskExtractionResult
from ax_agent_factory.infra.llm_client import (
    LLMClient,
    InvalidLLMJsonError,
    _extract_json_from_text,
)
from ax_agent_factory.infra.prompts import load_prompt

logger = logging.getLogger(__name__)


class IVCTaskExtractor:
    """IVC-A Task Extractor: 원자 과업 추출 전담."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient()

    def build_prompt(self, job_input: JobInput) -> str:
        """[IVC_TASK_EXTRACTOR_PROMPT_SPEC]에 따른 프롬프트 생성."""
        input_json = job_input.model_dump()
        template = load_prompt("ivc_task_extractor")
        return template.replace("{input_json}", json.dumps(input_json, ensure_ascii=False))

    def parse_response(self, raw_output: str) -> TaskExtractionResult:
        """LLM 응답(JSON 문자열 기대)을 파싱해 TaskExtractionResult로 변환."""
        logger.info("Parsing LLM JSON for ivc_task_extractor...")
        json_text = _extract_json_from_text(raw_output)
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            logger.error("Task Extractor JSON decoding failed", exc_info=True)
            raise InvalidLLMJsonError(
                "Failed to parse Task Extractor output as JSON",
                raw_text=raw_output,
                json_text=json_text,
            ) from exc

        if not isinstance(data, dict):
            raise InvalidLLMJsonError(
                "Task Extractor JSON is not an object",
                raw_text=raw_output,
                json_text=json_text,
            )

        try:
            result = parse_task_extraction_dict(data)
            logger.info("Task Extractor parsing succeeded. task_count=%d", len(result.task_atoms))
            return result
        except Exception:
            logger.error("Task Extractor payload validation failed", exc_info=True)
            raise

    def run(self, job_input: JobInput) -> TaskExtractionResult:
        """프롬프트 생성 → LLM 호출 → 파싱."""
        logger.info(
            "IVC TaskExtractor started for job_title=%s, company_name=%s",
            job_input.job_meta.job_title,
            job_input.job_meta.company_name,
        )
        prompt = self.build_prompt(job_input)
        try:
            logger.info("Calling ivc_task_extractor LLM...")
            raw_output = self.llm.call(prompt)
            logger.info(
                "LLM response received. length=%d, first_200_chars=%s",
                len(raw_output or ""),
                (raw_output or "")[:200],
            )
            return self.parse_response(raw_output)
        except InvalidLLMJsonError:
            # Bubble up with context; upstream can decide to fallback
            logger.error("Task Extractor JSON parsing error", exc_info=True)
            raise
        except NotImplementedError:
            logger.warning("LLM not implemented; returning stub result")
            # Fallback stub for environments without LLM connectivity
            return self._stub_result(job_input)

    def _stub_result(self, job_input: JobInput) -> TaskExtractionResult:
        """Generate a simple deterministic stub result if LLM is unavailable."""
        text = job_input.raw_job_desc.strip()
        task_atoms: list[IVCAtomicTask] = []
        if text:
            task_atoms.append(
                IVCAtomicTask(
                    task_id="T01",
                    task_original_sentence=text[:200],
                    task_korean=f"{job_input.job_meta.job_title} 업무 파악하기",
                    task_english="Understand role tasks",
                    notes="Stub result generated without LLM",
                )
            )
        else:
            task_atoms.append(
                IVCAtomicTask(
                    task_id="T01",
                    task_original_sentence="",
                    task_korean="업무 내용 수집하기",
                    task_english="collect tasks",
                    notes="Empty raw_job_desc stub",
                )
            )
        return TaskExtractionResult(job_meta=job_input.job_meta, task_atoms=task_atoms)


def parse_task_extraction_dict(payload: dict) -> TaskExtractionResult:
    """
    Pure conversion from dict to TaskExtractionResult for easier testing/validation.
    """
    return TaskExtractionResult(**payload)
