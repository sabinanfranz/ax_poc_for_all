# Parsing Guide
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 공통 원칙
- **JSON Only**: LLM 응답은 단일 JSON 객체. 코드블록/서술을 `_extract_json_from_text` → `_parse_json_candidates`로 정규화.
- **내결함성**: 경미한 문법 오류(여분의 `}` 등)는 Stage별 sanitizer로 완화하고, 여전히 실패하면 스텁을 반환하며 `llm_error`에 사유를 남긴다.
- **디버그 필드**: 결과 모델에 `llm_raw_text`, `llm_cleaned_json`, `llm_error`를 붙여 UI/테스트/로그에서 동일하게 확인.
- **스텁 정책**: SDK/키 미존재 또는 파싱 실패 시 stub_fallback/json_parse_error 상태로 반환해 파이프라인을 끊지 않는다.

## 주요 파서/유틸 (infra/llm_client.py)
- `_extract_json_from_text(text)`: 코드펜스/서술 제거 후 JSON 후보만 슬라이스.
- `_parse_json_candidates(text)`: 정규화된 여러 문자열 후보를 순차 파싱; 성공 시 `(dict, cleaned_text)` 반환.
- `_normalize_json_text(text)`: BOM/개행/따옴표 정규화 및 trailing comma 제거.
- `_sanitize_task_extractor_text(text)`: Task Extractor용 경미한 치유(예: `raw_job_desc` 뒤 잘못 닫힌 `}` 제거).
- `_sanitize_phase_classifier_text(text)`: Phase Classifier용 경미한 치유(동일 패턴 적용).
- `_sanitize_workflow_text(text)`: Workflow Struct/Mermaid용 경미한 치유(동일 패턴 적용).
- `_generic_llm_json_call(...)`: Workflow Struct/Mermaid/Static 등에서 재사용되는 공통 JSON 호출기(스텁/로깅/파싱 일관화).

## Stage별 파싱 흐름
- **0.1/0.2** (`call_job_research_collect|summarize`): `_extract_json_from_text` → `_parse_json_candidates` → dict 반환 → Pydantic 변환 없음(단순 dict) → DB 저장.
- **1-A** (`call_task_extractor`): sanitizer → `_parse_json_candidates` → `parse_task_extraction_dict`로 Pydantic 검증 → 실패 시 스텁.
- **1-B** (`call_phase_classifier`): sanitizer → `_parse_json_candidates` → `parse_phase_classification_dict`로 Pydantic 검증 → 실패 시 스텁.
- **1.3** (`call_static_task_classifier`): `_generic_llm_json_call` → `_sanitize_phase_classifier_text` → `_parse_json_candidates` → `StaticClassificationResult`로 검증 → 실패 시 스텁.
- **2.1/2.2** (`call_workflow_struct|mermaid`): `_generic_llm_json_call` → `_sanitize_workflow_text` → `_parse_json_candidates` → Pydantic(`WorkflowPlan`/`MermaidDiagram`)로 검증 → 실패/키 없음 시 스텁.

## 프롬프트 작성 팁
- 입력 JSON은 `{input_json}` 치환을 사용하고, 허용된 top-level 키만 명시.
- 출력 스키마를 프롬프트에 적시하고, “코드블록 금지/JSON 하나만”을 반복 강조.
- 선택적 필드는 명시적으로 `null` 허용을 적어 LLM이 키를 누락하지 않도록 한다.

## 테스트 체크리스트
- 깨끗한 JSON, fenced JSON, 서술 섞인 JSON 모두 파싱 성공.
- 경미한 문법 오류(잘못 닫힌 `}` 등) → sanitizer로 복구 후 파싱 성공.
- 강한 오류 → 스텁 반환 + `llm_error` 세팅, 파이프라인은 중단되지 않음.
- 결과 객체의 디버그 필드(`llm_raw_text/llm_cleaned_json/llm_error`)가 채워지는지 확인.
