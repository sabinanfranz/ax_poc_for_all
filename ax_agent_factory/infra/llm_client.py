"""LLM client wrapper for AX Agent Factory (Gemini web-browsing)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

try:  # Optional dependency for runtime; tests can monkeypatch this module.
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - handled by stub fallback
    genai = None  # type: ignore
    types = None  # type: ignore


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
        raise NotImplementedError("LLM API 연동은 별도 구현 예정")


def call_gemini_job_research(
    company_name: str,
    job_title: str,
    manual_jd_text: str | None = None,
    max_tokens: int = 4096,
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

    prompt = f"""
    [역할]
    당신은 Job Research 전문 에이전트입니다. Google Search web_browsing 도구를 사용해 직무 설명을 수집/통합합니다.

    [입력]
    - 회사명: {company_name}
    - 직무명: {job_title}
    - 수동 JD 텍스트: {manual_jd_text or '제공되지 않음'}

    [출력 요구]
    JSON 한 개만 반환하세요. 마크다운/설명 없이 순수 JSON.
    {{
      "raw_job_desc": "string",
      "research_sources": [
        {{"url": "string", "title": "string", "snippet": "string", "source_type": "jd | article | company_page | etc", "score": 0.0}}
      ]
    }}
    """.strip()

    if genai is None or os.environ.get("GOOGLE_API_KEY") is None:
        # Stub fallback when SDK/key unavailable
        return {
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

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        max_output_tokens=max_tokens,
    )

    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=config,
    )

    raw_text = getattr(response, "text", "") or ""
    try:
        parsed = json.loads(raw_text)
    except Exception as exc:  # pragma: no cover - depends on runtime response
        raise ValueError(f"Gemini 응답을 JSON으로 파싱할 수 없습니다: {raw_text[:200]}") from exc

    return parsed
