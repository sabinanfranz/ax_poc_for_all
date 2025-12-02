# Gemini 모델 사용 가이드
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## 현재 프로젝트에서 사용하는 모델
- **Stage 0 Job Research**: `GEMINI_MODEL` 환경변수(기본 `gemini-2.5-flash`)를 사용해 web_browsing 호출. google-genai SDK 또는 환경변수가 없으면 스텁 결과를 반환한다.
- **Stage 1 IVC**: `LLMClient`가 준비돼 있으나 `call()`이 NotImplementedError로 남아 있다. 실제 모델을 연결하려면 구현/교체가 필요하며, 기본 스텁은 LLM 없이도 동작 확인용으로 쓰인다.

## 호출 방식 요약 (`infra/llm_client.py`)
- `call_gemini_job_research(...)`
  - 도구: `google_search` Tool.
  - 출력: JSON 텍스트(코드펜스 제거 → JSON 파싱). 실패 시 `_stub_job_research`.
  - 환경변수: `GOOGLE_API_KEY`, `GEMINI_MODEL`(미설정 시 `gemini-2.5-flash`).
- `_extract_json_from_text`
  - 코드펜스/여분 서술을 제거하고 첫 `{`~마지막 `}`만 슬라이스하는 유틸. JSONDecodeError 방지용.

## 모델 선택 가이드 (실사용 시)
- **추천 기본값**: `gemini-2.5-flash` (web_browsing 지원, 속도/비용 균형).
- **대체 옵션**
  - 비용 절감: `gemini-2.5-flash-lite` (web_browsing 미지원이므로 Stage 0에는 부적합).
  - 품질 우선: `gemini-2.5-pro` (비용 증가, web_browsing 지원 여부 확인 필요).
- web_browsing이 필요한 프롬프트에는 web_search가 지원되는 모델만 사용한다.

## 연결 체크리스트
1) `pip install google-genai` 설치 여부 확인.  
2) `GOOGLE_API_KEY` 설정.  
3) `GEMINI_MODEL`이 web_search 지원 모델인지 확인.  
4) 파싱 실패 시 UI의 “LLM 응답/에러” 탭과 `logs/app.log`를 확인한다.
