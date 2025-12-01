"""IVC Task Extractor module (Stage 1.1)."""

from __future__ import annotations

import json
from typing import Optional

from ax_agent_factory.core.schemas.common import JobInput, TaskExtractionResult, IVCAtomicTask
from ax_agent_factory.infra.llm_client import LLMClient
from ax_agent_factory.infra.prompts import load_prompt


class IVCTaskExtractor:
    """IVC-A Task Extractor: 원자 과업 추출 전담."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient()

    def build_prompt(self, job_input: JobInput) -> str:
        """[IVC_TASK_EXTRACTOR_PROMPT_SPEC]에 따른 프롬프트 생성."""
        input_json = job_input.dict()
        template = load_prompt("ivc_task_extractor")
        return template.format(input_json=json.dumps(input_json, ensure_ascii=False))

    def parse_response(self, raw_output: str) -> TaskExtractionResult:
        """LLM 응답(JSON 문자열 기대)을 파싱해 TaskExtractionResult로 변환."""
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse Task Extractor output as JSON: {exc}") from exc
        return TaskExtractionResult(**data)

    def run(self, job_input: JobInput) -> TaskExtractionResult:
        """프롬프트 생성 → LLM 호출 → 파싱."""
        prompt = self.build_prompt(job_input)
        try:
            raw_output = self.llm.call(prompt)
            return self.parse_response(raw_output)
        except NotImplementedError:
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
