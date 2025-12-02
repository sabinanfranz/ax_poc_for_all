# Gemini 모델 사용 가이드
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## 현재 프로젝트에서 사용하는 모델
- **Stage 0 Job Research**: `GEMINI_MODEL` 환경변수(기본 `gemini-2.5-flash`)를 사용해 web_browsing 호출. google-genai SDK 또는 환경변수가 없으면 스텁 결과를 반환한다.
- **Stage 1 IVC**: `call_task_extractor` / `call_phase_classifier`가 Gemini를 직접 호출(키 없으면 스텁). 공용 `LLMClient.call`는 여전히 NotImplemented 상태지만 Stage 1 경로에서는 사용하지 않는다.

## 호출 방식 요약 (`infra/llm_client.py`)
- `call_gemini_job_research(...)`, `call_job_research_collect(...)`, `call_job_research_summarize(...)`, `call_task_extractor(...)`, `call_phase_classifier(...)`
  - 도구: Stage 0.x는 `google_search` Tool, Stage 1은 텍스트 모델 호출.
  - 출력: JSON 텍스트를 `_extract_json_from_text` → `_parse_json_candidates`(경미한 sanitizer 포함)로 파싱. 실패 시 스텁 반환.
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
