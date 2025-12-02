"""LLM client wrapper for AX Agent Factory (Gemini web-browsing)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional

from ax_agent_factory.infra.prompts import load_prompt
from ax_agent_factory.infra import db
from ax_agent_factory.models.llm_log import LLMCallLog

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
        _safe_save_llm_log(
            stage_name="llm_client_call",
            job_run_id=None,
            model_name=self.model_name,
            prompt_version=None,
            temperature=temperature,
            top_p=None,
            input_payload_json=json.dumps(
                {"prompt": prompt, "model": self.model_name, "temperature": temperature},
                ensure_ascii=False,
            ),
            output_text_raw=None,
            output_json_parsed=None,
            status="not_implemented",
            error_type="NotImplementedError",
            error_message="LLM API not implemented",
            latency_ms=None,
        )
        raise NotImplementedError("LLM API 연동은 별도 구현 예정")


DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def call_gemini_job_research(
    company_name: str,
    job_title: str,
    manual_jd_text: str | None = None,
    max_tokens: int = 16384,
    *,
    model: str | None = None,
    job_run_id: Optional[int] = None,
    stage_name: str = "stage0_legacy",
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

    started = time.time()
    input_payload = {
        "company_name": company_name,
        "job_title": job_title,
        "manual_jd_text": manual_jd_text,
        "prompt": prompt,
        "model": model or DEFAULT_GEMINI_MODEL,
        "max_output_tokens": max_tokens,
        "tools": ["google_search"],
    }
    raw_text = ""
    cleaned = ""

    if genai is None or os.environ.get("GOOGLE_API_KEY") is None:
        logger.warning("google-genai SDK or GOOGLE_API_KEY missing; returning stub job research result")
        stub = _stub_job_research(company_name, job_title, _raw_text="", _cleaned_json="")
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=None,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="stub_fallback",
            error_type=None,
            error_message=None,
            latency_ms=_elapsed_ms(started),
        )
        return stub

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        max_output_tokens=max_tokens,
    )

    logger.info("Calling Gemini job_research model=%s", model or DEFAULT_GEMINI_MODEL)
    try:
        response = client.models.generate_content(
            model=model or DEFAULT_GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=config,
        )
        raw_text = _extract_text_from_response(response)
        logger.info("Gemini raw response received. length=%d", len(raw_text))
        cleaned = _normalize_json_text(_clean_json_text(raw_text))
        parsed = json.loads(cleaned, strict=False)
        parsed["_raw_text"] = raw_text
        parsed["_cleaned_json"] = cleaned
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=None,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(parsed, ensure_ascii=False),
            status="success",
            error_type=None,
            error_message=None,
            latency_ms=_elapsed_ms(started),
        )
        return parsed
    except Exception as exc:  # pragma: no cover - depends on runtime response
        logger.error("Job research JSON parsing failed; returning stub", exc_info=True)
        stub = _stub_job_research(
            company_name,
            job_title,
            llm_error=str(exc),
            _raw_text=raw_text,
            _cleaned_json=cleaned,
        )
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=None,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="json_parse_error",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            latency_ms=_elapsed_ms(started),
        )
        return stub


def call_job_research_collect(
    company_name: str,
    job_title: str,
    manual_jd_text: str | None = None,
    max_tokens: int = 16384,
    *,
    model: str | None = None,
    job_run_id: Optional[int] = None,
    stage_name: str = "stage0_collect",
    prompt_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Stage 0.1 Web Research Collector: gather raw_sources only."""
    logger.info("call_job_research_collect started for company=%s, job_title=%s", company_name, job_title)
    prompt_template = _load_prompt("job_research_collect")
    replacements = {
        "company_name": company_name,
        "job_title": job_title,
        "manual_jd_text": manual_jd_text or "제공되지 않음",
    }
    prompt = prompt_template
    for key, val in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))

    started = time.time()
    input_payload = {
        "company_name": company_name,
        "job_title": job_title,
        "manual_jd_text": manual_jd_text,
        "prompt": prompt,
        "model": model or DEFAULT_GEMINI_MODEL,
        "max_output_tokens": max_tokens,
        "tools": ["google_search"],
    }
    raw_text = ""
    cleaned = ""

    if genai is None or os.environ.get("GOOGLE_API_KEY") is None:
        logger.warning("google-genai SDK or GOOGLE_API_KEY missing; returning stub collect result")
        stub = _stub_job_research_collect(company_name, job_title, _raw_text="", _cleaned_json="")
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="stub_fallback",
            error_type=None,
            error_message=None,
            latency_ms=_elapsed_ms(started),
        )
        return stub

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        max_output_tokens=max_tokens,
    )

    logger.info("Calling Gemini job_research_collect model=%s", model or DEFAULT_GEMINI_MODEL)
    try:
        response = client.models.generate_content(
            model=model or DEFAULT_GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=config,
        )

        raw_text = _extract_text_from_response(response)
        logger.info("Collect raw response received. length=%d", len(raw_text))
        parsed, cleaned = _parse_json_candidates(raw_text)
        if parsed is None:
            raise InvalidLLMJsonError("Failed to parse collect JSON", raw_text=raw_text, json_text=cleaned)
        parsed["_raw_text"] = raw_text
        parsed["_cleaned_json"] = cleaned
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(parsed, ensure_ascii=False),
            status="success",
            error_type=None,
            error_message=None,
            latency_ms=_elapsed_ms(started),
        )
        return parsed
    except InvalidLLMJsonError as exc:
        logger.warning("Collect JSON parsing failed; returning stub", exc_info=False)
        stub = _stub_job_research_collect(
            company_name,
            job_title,
            llm_error=str(exc),
            _raw_text=raw_text,
            _cleaned_json=cleaned,
        )
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="json_parse_error",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            latency_ms=_elapsed_ms(started),
        )
        return stub
    except Exception as exc:  # pragma: no cover - runtime dependent
        logger.error("Collect JSON parsing failed; returning stub", exc_info=True)
        stub = _stub_job_research_collect(
            company_name,
            job_title,
            llm_error=str(exc),
            _raw_text=raw_text,
            _cleaned_json=cleaned,
        )
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="json_parse_error",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            latency_ms=_elapsed_ms(started),
        )
        return stub


def call_job_research_summarize(
    job_meta: Dict[str, Any],
    raw_sources: list[Dict[str, Any]],
    manual_jd_text: str | None = None,
    max_tokens: int = 16384,
    *,
    model: str | None = None,
    job_run_id: Optional[int] = None,
    stage_name: str = "stage0_summarize",
    prompt_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Stage 0.2 Task-Oriented Synthesizer: merge raw_sources into raw_job_desc + research_sources."""
    logger.info("call_job_research_summarize started for job_title=%s", job_meta.get("job_title"))
    prompt_template = _load_prompt("job_research_summarize")
    replacements = {
        "job_meta_json": json.dumps(job_meta, ensure_ascii=False),
        "raw_sources_json": json.dumps(raw_sources, ensure_ascii=False),
        "manual_jd_text": manual_jd_text or "제공되지 않음",
    }
    prompt = prompt_template
    for key, val in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))

    started = time.time()
    input_payload = {
        "job_meta": job_meta,
        "raw_sources": raw_sources,
        "manual_jd_text": manual_jd_text,
        "prompt": prompt,
        "model": model or DEFAULT_GEMINI_MODEL,
        "max_output_tokens": max_tokens,
    }
    raw_text = ""
    cleaned = ""

    if genai is None or os.environ.get("GOOGLE_API_KEY") is None:
        logger.warning("google-genai SDK or GOOGLE_API_KEY missing; returning stub summarize result")
        stub = _stub_job_research_summarize(job_meta, raw_sources, _raw_text="", _cleaned_json="")
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="stub_fallback",
            error_type=None,
            error_message=None,
            latency_ms=_elapsed_ms(started),
        )
        return stub

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    config = types.GenerateContentConfig(max_output_tokens=max_tokens)

    logger.info("Calling Gemini job_research_summarize model=%s", model or DEFAULT_GEMINI_MODEL)
    try:
        response = client.models.generate_content(
            model=model or DEFAULT_GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=config,
        )

        raw_text = _extract_text_from_response(response)
        logger.info("Summarize raw response received. length=%d", len(raw_text))
        parsed, cleaned = _parse_json_candidates(raw_text)
        if parsed is None:
            raise InvalidLLMJsonError(
                "Failed to parse summarize JSON",
                raw_text=raw_text,
                json_text=cleaned,
            )
        parsed["_raw_text"] = raw_text
        parsed["_cleaned_json"] = cleaned
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(parsed, ensure_ascii=False),
            status="success",
            error_type=None,
            error_message=None,
            latency_ms=_elapsed_ms(started),
        )
        return parsed
    except InvalidLLMJsonError as exc:
        logger.warning("Summarize JSON parsing failed; returning stub", exc_info=False)
        stub = _stub_job_research_summarize(
            job_meta,
            raw_sources,
            llm_error=str(exc),
            _raw_text=raw_text,
            _cleaned_json=cleaned,
        )
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="json_parse_error",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            latency_ms=_elapsed_ms(started),
        )
        return stub
    except Exception as exc:  # pragma: no cover - runtime dependent
        logger.error("Summarize JSON parsing failed; returning stub", exc_info=True)
        stub = _stub_job_research_summarize(
            job_meta,
            raw_sources,
            llm_error=str(exc),
            _raw_text=raw_text,
            _cleaned_json=cleaned,
        )
        _safe_save_llm_log(
            stage_name=stage_name,
            job_run_id=job_run_id,
            model_name=model or DEFAULT_GEMINI_MODEL,
            prompt_version=prompt_version,
            temperature=None,
            top_p=None,
            input_payload_json=json.dumps(input_payload, ensure_ascii=False),
            output_text_raw=raw_text,
            output_json_parsed=json.dumps(stub, ensure_ascii=False),
            status="json_parse_error",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            latency_ms=_elapsed_ms(started),
        )
        return stub


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
    # propagate raw/cleaned text for UI when available
    if "_raw_text" not in stub and "raw_text" in stub:
        stub["_raw_text"] = stub["raw_text"]
    return stub


def _stub_job_research_collect(company_name: str, job_title: str, **extra: Any) -> Dict[str, Any]:
    """Stub for Stage 0.1 collect."""
    stub = {
        "raw_sources": [
            {
                "url": "https://example.com/jd",
                "title": f"{company_name} {job_title} JD",
                "snippet": "Example snippet about tasks/tools",
                "source_type": "jd",
                "score": 0.5,
            }
        ],
    }
    if extra:
        stub.update(extra)
    if "_raw_text" not in stub and "raw_text" in stub:
        stub["_raw_text"] = stub["raw_text"]
    return stub


def _stub_job_research_summarize(
    job_meta: Dict[str, Any],
    raw_sources: list[Dict[str, Any]],
    **extra: Any,
) -> Dict[str, Any]:
    """Stub for Stage 0.2 summarize."""
    company_name = job_meta.get("company_name", "회사")
    job_title = job_meta.get("job_title", "직무")
    stub = {
        "raw_job_desc": f"{company_name} {job_title} 역할에 대한 예시 직무 설명 (stub)",
        "research_sources": raw_sources
        or [
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
    if "_raw_text" not in stub and "raw_text" in stub:
        stub["_raw_text"] = stub["raw_text"]
    return stub


def _parse_json_candidates(raw_text: str) -> tuple[dict | None, str]:
    """
    Try multiple normalized candidates to parse JSON; return (parsed, cleaned_text).
    Order:
    1) normalized(clean(extract(raw_text)))
    2) clean(extract(raw_text))
    3) raw_text stripped
    """
    candidates: list[str] = []
    primary = _normalize_json_text(_clean_json_text(raw_text))
    if primary:
        candidates.append(primary)
    secondary = _clean_json_text(raw_text)
    if secondary and secondary not in candidates:
        candidates.append(secondary)
    stripped = (raw_text or "").strip()
    if stripped and stripped not in candidates:
        candidates.append(stripped)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate, strict=False)
            return parsed, candidate
        except Exception:
            continue
    return None, primary if candidates else ""


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


def _extract_text_from_response(response: Any) -> str:
    """Safely extract text from google-genai response even when .text is empty."""
    text = getattr(response, "text", None)
    if text:
        return text

    candidates = getattr(response, "candidates", None) or []
    collected: list[str] = []
    for cand in candidates:
        content = getattr(cand, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                collected.append(part_text)

    return "\n".join(collected).strip()


def _normalize_json_text(text: str) -> str:
    """
    Normalize LLM JSON-ish text before parsing:
    - strip BOM/whitespace
    - de-curly quotes
    - escape bare newlines inside quoted strings
    - drop trailing commas before } or ]
    """
    normalized = (text or "").replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    normalized = (
        normalized.replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
        .replace("\xa0", " ")
    )
    normalized = _escape_newlines_in_strings(normalized)
    normalized = re.sub(r",(\s*[}\]])", r"\1", normalized)
    return normalized


def _escape_newlines_in_strings(text: str) -> str:
    """Escape raw newlines that appear inside double-quoted JSON strings."""
    def _replace(match: re.Match[str]) -> str:
        segment = match.group(0)
        return segment.replace("\n", "\\n")

    return re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', _replace, text)


def _elapsed_ms(started: float) -> int:
    """Helper to compute latency in ms."""
    return int((time.time() - started) * 1000)


def _safe_save_llm_log(
    *,
    stage_name: str,
    job_run_id: Optional[int],
    model_name: str,
    prompt_version: Optional[str],
    temperature: Optional[float],
    top_p: Optional[float],
    input_payload_json: str,
    output_text_raw: Optional[str],
    output_json_parsed: Optional[str],
    status: str,
    error_type: Optional[str],
    error_message: Optional[str],
    latency_ms: Optional[int],
    agent_name: Optional[str] = None,
    tokens_prompt: Optional[int] = None,
    tokens_completion: Optional[int] = None,
    tokens_total: Optional[int] = None,
) -> None:
    """Persist LLM call log without interrupting main flow."""
    try:
        log = LLMCallLog(
            created_at=datetime.utcnow().isoformat(),
            job_run_id=job_run_id,
            stage_name=stage_name,
            agent_name=agent_name,
            model_name=model_name,
            prompt_version=prompt_version,
            temperature=temperature,
            top_p=top_p,
            input_payload_json=input_payload_json,
            output_text_raw=output_text_raw,
            output_json_parsed=output_json_parsed,
            status=status,
            error_type=error_type,
            error_message=error_message,
            latency_ms=latency_ms,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tokens_total=tokens_total,
        )
        db.save_llm_call_log(log)
    except Exception:  # pragma: no cover - logging must not break flow
        logger.exception("Failed to persist LLM call log")
