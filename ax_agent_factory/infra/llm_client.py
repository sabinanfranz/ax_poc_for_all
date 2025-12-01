"""LLM client wrapper for AX Agent Factory (Gemini web-browsing)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

from ax_agent_factory.infra.prompts import load_prompt

try:  # Optional dependency for runtime; tests can monkeypatch this module.
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - handled by stub fallback
    genai = None  # type: ignore
    types = None  # type: ignore


logger = logging.getLogger(__name__)


class InvalidLLMJsonError(ValueError):
    """Raised when LLM text cannot be converted into valid JSON."""

    def __init__(self, message: str, *, raw_text: str, json_text: Optional[str] = None) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.json_text = json_text


class LLMClient:
    """
    공통 LLM 클라이언트 스텁. 실제 API 연동은 추후 구현.
    """

    def __init__(self, model_name: str = "gpt-4.1") -> None:
        self.model_name = model_name

    def call(self, prompt: str, *, temperature: float = 0.2) -> str:
        """
        실제 LLM API 호출을 감싸는 래퍼.
        v1 PoC에서는 실제 API 호출 대신, NotImplementedError를 발생시킵니다.
        """
        logger.info("LLMClient.call invoked with model=%s", self.model_name)
        logger.debug("LLM prompt preview (first 200 chars): %s", prompt[:200])
        raise NotImplementedError("LLM API 연동은 별도 구현 예정")


DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def call_gemini_job_research(
    company_name: str,
    job_title: str,
    manual_jd_text: str | None = None,
    max_tokens: int = 4096,
    *,
    model: str | None = None,
) -> Dict[str, Any]:
    """
    Gemini 1.5 Pro + web_browsing tool을 사용해 직무 리서치를 수행한다.

    주된 역할:
      1) 회사명 + 직무명으로 검색 쿼리를 구성
      2) web_browsing tool로 JD/직무 설명, 블로그, 채용사이트 등을 검색
      3) 여러 소스를 요약하여 raw_job_desc 생성
      4) 각 소스의 url/title/snippet/meta를 research_sources 리스트로 반환

    반환 형식:
      {
        "raw_job_desc": "... 긴 한국어 직무 설명 ...",
        "research_sources": [
          {
            "url": "...",
            "title": "...",
            "snippet": "...",
            "source_type": "jd | article | company_page | etc",
            "score": 0.87
          },
          ...
        ]
      }

    GOOGLE_API_KEY 환경변수로 인증하며, google-genai SDK가 없거나 키가 없으면 스텁을 반환한다.
    """

    logger.info("call_gemini_job_research started for company=%s, job_title=%s", company_name, job_title)
    prompt_template = _load_prompt("job_research")
    replacements = {
        "company_name": company_name,
        "job_title": job_title,
        "manual_jd_text": manual_jd_text or "제공되지 않음",
    }
    prompt = prompt_template
    for key, val in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))

    if genai is None or os.environ.get("GOOGLE_API_KEY") is None:
        logger.warning("google-genai SDK or GOOGLE_API_KEY missing; returning stub job research result")
        return _stub_job_research(company_name, job_title)

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        max_output_tokens=max_tokens,
    )

    logger.info("Calling Gemini job_research model=%s", model or DEFAULT_GEMINI_MODEL)
    response = client.models.generate_content(
        model=model or DEFAULT_GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=config,
    )

    raw_text = getattr(response, "text", "") or ""
    logger.info("Gemini raw response received. length=%d", len(raw_text))
    cleaned = _clean_json_text(raw_text)
    try:
        parsed = json.loads(cleaned)
        parsed["_raw_text"] = raw_text  # include raw text for UI/debug
        return parsed
    except Exception as exc:  # pragma: no cover - depends on runtime response
        logger.error("Job research JSON parsing failed; returning stub", exc_info=True)
        return _stub_job_research(
            company_name,
            job_title,
            llm_error=str(exc),
            raw_text=raw_text[:1000],
        )


def _stub_job_research(company_name: str, job_title: str, **extra: Any) -> Dict[str, Any]:
    """Return stubbed Job Research output when LLM is unavailable or parsing fails."""
    stub = {
        "raw_job_desc": f"{company_name} {job_title} 역할에 대한 예시 직무 설명 (stub)",
        "research_sources": [
            {
                "url": "https://example.com/jd",
                "title": f"{company_name} {job_title} JD",
                "snippet": "Example snippet",
                "source_type": "jd",
                "score": 0.5,
            }
        ],
    }
    if extra:
        stub.update(extra)
    return stub


def _clean_json_text(raw_text: str) -> str:
    """
    Deprecated helper kept for backward compatibility.

    Delegates to the more robust _extract_json_from_text to strip fences and
    trim surrounding explanations.
    """
    return _extract_json_from_text(raw_text)


def _load_prompt(name: str) -> str:
    """Wrapper to load prompt templates from prompts package."""
    return load_prompt(name)


def _extract_json_from_text(text: str) -> str:
    """
    Extract JSON substring from LLM text that may include code fences or narration.

    - If ```json ... ``` or ``` ... ``` fences exist, return the inner block.
    - Else, if braces exist, slice from first '{' to last '}'.
    - Otherwise, return stripped text.
    """
    if not isinstance(text, str):
        raise InvalidLLMJsonError("LLM output is not a string", raw_text=str(text), json_text=None)

    stripped = text.strip()

    fence_match = re.findall(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match[0].strip()
        if candidate:
            return candidate

    if "{" in stripped and "}" in stripped:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1].strip()

    return stripped
