"""IVC Task Extractor module (Stage 1.1)."""

from __future__ import annotations

import json
import logging
from typing import Optional

from ax_agent_factory.core.schemas.common import IVCAtomicTask, JobInput, TaskExtractionResult
from ax_agent_factory.infra.llm_client import (
    LLMClient,
    InvalidLLMJsonError,
    call_task_extractor,
)
from ax_agent_factory.infra.prompts import load_prompt
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class IVCTaskExtractor:
    """IVC-A Task Extractor: 원자 과업 추출 전담."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client

    def build_prompt(self, job_input: JobInput) -> str:
        """[IVC_TASK_EXTRACTOR_PROMPT_SPEC]에 따른 프롬프트 생성."""
        input_json = job_input.model_dump()
        template = load_prompt("ivc_task_extractor")
        return template.replace("{input_json}", json.dumps(input_json, ensure_ascii=False))

    def run(self, job_input: JobInput, *, job_run_id: Optional[int] = None) -> TaskExtractionResult:
        """프롬프트 생성 → LLM 호출 → 파싱."""
        logger.info(
            "IVC TaskExtractor started for job_title=%s, company_name=%s",
            job_input.job_meta.job_title,
            job_input.job_meta.company_name,
        )
        try:
            llm_output = call_task_extractor(
                job_input.model_dump(),
                job_run_id=job_run_id,
                llm_client_override=self.llm,
            )
            result = parse_task_extraction_dict(llm_output)
            # attach debug fields for UI (not persisted)
            if hasattr(result, "llm_raw_text"):
                result.llm_raw_text = llm_output.get("_raw_text")  # type: ignore[attr-defined]
                result.llm_cleaned_json = llm_output.get("_cleaned_json")  # type: ignore[attr-defined]
                result.llm_error = llm_output.get("llm_error")  # type: ignore[attr-defined]
            logger.info("Task Extractor parsing succeeded. task_count=%d", len(result.task_atoms))
            return result
        except InvalidLLMJsonError:
            logger.error("Task Extractor JSON parsing error", exc_info=True)
            return self._stub_result(job_input)
        except ValidationError as exc:
            logger.warning("Task Extractor validation failed; returning stub", exc_info=False)
            stub = self._stub_result(job_input)
            if hasattr(stub, "llm_error"):
                stub.llm_error = str(exc)  # type: ignore[attr-defined]
            return stub
        except Exception:
            logger.error("Task Extractor unexpected error", exc_info=True)
            raise

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
