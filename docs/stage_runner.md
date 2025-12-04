# Stage Runner 패턴
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 개념
- 모든 Stage(0.1 Collect, 0.2 Summarize, 1-A Task Extractor, 1-B Phase Classifier)가 공유하는 **입력 정규화 → 프롬프트/LLM 호출 → JSON 정규화/파싱 → 스키마 검증 → 디버그 필드 부착 → 캐시/로깅 → 다음 Stage 전달** 흐름을 일관 패턴으로 정의한다.
- 핵심 목표: 실패해도 끊기지 않고(stub), UI/로그/DB에서 같은 필드명으로 추적 가능하게 유지.

## 실행 라이프사이클
1) **입력 수집/정규화**: Pydantic/dataclass를 JSON(dict)으로 직렬화. 필요 시 job_run_id, prompt_version, model_name, manual_jd_text 포함.
2) **프롬프트 구성**: `prompts/<stage>.txt`에 `{input_json}` 혹은 개별 플레이스홀더를 채워 넣는다.
3) **LLM 호출**: `infra.llm_client.call_<stage>` 헬퍼를 사용. 옵션: model, max_tokens(기본 81920), llm_client_override(테스트/페이크), job_run_id, stage_name, prompt_version.
4) **JSON 정규화/파싱**: `_extract_json_from_text` → `_parse_json_candidates` 로 코드펜스/서술을 제거하고 여러 후보를 순차 파싱(Workflow는 `_sanitize_workflow_text` 포함).
5) **검증/변환**: Stage별 `parse_*_dict` 또는 Pydantic 스키마(`WorkflowPlan`, `MermaidDiagram`, `StaticClassificationResult`)로 변환.
6) **디버그 부착**: `_raw_text`/`_cleaned_json`/`llm_error`를 결과 객체에 `llm_raw_text`/`llm_cleaned_json`/`llm_error`로 복사(UI/테스트용).
7) **저장/전달**: Stage 0.1/0.2는 DB 저장, Stage 1/1.3/2는 메모리 전달 + `job_tasks`/`job_task_edges` 업데이트. 다음 Stage 입력으로 필요한 최소 필드를 그대로 복사.
8) **로깅**: `llm_call_logs`에 stage_name/status(stub_fallback/json_parse_error/success) 기록.

## 실패/스텁 정책
- google-genai SDK 미존재 또는 `GOOGLE_API_KEY` 미설정 → 즉시 stub_fallback.
- JSON 파싱 실패 → `InvalidLLMJsonError` 로 감싸고 stub 반환(`llm_error` 설정).
- 스텁은 입력을 최대한 복사하고 최소 필수 필드만 채워 다음 Stage가 중단 없이 돌도록 한다.

## 공통 계약 (필수 필드)
- 입력 키: `{input_json}` 혹은 명시적 `job_meta`, `raw_sources`, `raw_job_desc`, `task_atoms` 등 Stage별 스키마.
- 출력 디버그 키: `_raw_text`, `_cleaned_json`, `llm_error` (헬퍼 내부에서 결과 dict에 포함).
- UI/스키마 디버그 필드: `llm_raw_text`, `llm_cleaned_json`, `llm_error`.
- LLM JSON 규칙: 단일 JSON 객체, 코드블록/서술 금지, 허용된 top-level 키만 사용.

## 테스트 체크리스트
- 정상 JSON, fenced JSON, 서술 섞인 JSON → 파싱 성공.
- 잘못된 JSON → `json_parse_error` 상태, stub 반환, `llm_error` 세팅.
- 디버그 필드 노출: 결과 객체에 raw/cleaned/error 존재 확인.
- 파이프라인 연계: 이전 Stage 출력이 다음 Stage 입력에 그대로 복사되는지 검증.

## 적용 지침
- 새 Stage 추가 시: `call_<stage>` 헬퍼 생성 → 스텁/로깅/파싱 로직 포함 → 결과 스키마에 디버그 필드 정의 → UI 탭에 Input/결과/LLM/에러를 동일 필드명으로 노출.
- 프롬프트 변경 시: `{input_json}` 계약을 깨지 않도록 유지하고 `docs/iteration_log.md`에 기록.
