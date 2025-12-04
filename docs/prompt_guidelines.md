# AX Agent Factory – Prompt Guidelines
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 공통 원칙
- **JSON Only**: 출력은 하나의 JSON 객체. 코드블록(````), 설명 텍스트 금지.
- **역할/목표/포맷을 앞단에 명시**: 프롬프트 시작에 역할, 해야 할 일, 허용 top-level 키를 적는다.
- **스키마 복사**: 입력 `job_meta`, `task_atoms` 등은 “그대로 복사” 규칙을 명시.
- **에러 방지 문구**: “마크다운 코드블록을 쓰지 않는다”, “허용된 top-level 키 목록”을 적어 LLM이 벗어나지 않도록 한다.
- **프롬프트 저장 위치**: `ax_agent_factory/prompts/*.txt`, 로더 `infra/prompts.load_prompt`(LRU 캐시).

## Stage별 가이드
- **Stage 0 – Job Research**
  - 0.1 Collect (`prompts/job_research_collect.txt`): web_browsing 전제, 업무/프로젝트/툴 중심 소스만 수집.
  - 0.2 Summarize (`prompts/job_research_summarize.txt`): `raw_sources`를 통합해 `raw_job_desc`를 작성하고 핵심 `research_sources`만 남김.
  - 출력 키는 각각 `raw_sources` / `raw_job_desc`, `research_sources`로 제한.
- **Stage 1-A – IVC Task Extractor (`prompts/ivc_task_extractor.txt`)**
  - 과업 표현을 `[대상] [동사]하기`로 통일, 목적 제거.
  - 출력 키: `job_meta`, `task_atoms[]`(task_id, task_original_sentence, task_korean, task_english, notes). `raw_job_desc`를 출력에 포함하지 않도록 명시.
- **Stage 1-B – IVC Phase Classifier (`prompts/ivc_phase_classifier.txt`)**
  - 입력의 `job_meta/raw_job_desc/task_atoms`를 그대로 복사하도록 명시.
  - 출력 키: `job_meta`, `raw_job_desc`, `task_atoms`, `ivc_tasks`, `phase_summary` 외 금지.
  - Phase 정의/규칙을 짧게 제시하고, reason을 한국어 1~2문장으로 요구.
  - 주의: 예시는 `phase/reason` 등을 사용하지만, 스키마는 `ivc_phase/ivc_exec_subphase/primitive_lv1/classification_reason`을 기대하므로 프롬프트를 스키마에 맞춰 유지.
- **Stage 1.3 – Static Task Classifier (`prompts/static_task_classifier.txt`)**
  - 입력: PhaseClassificationResult 전체(dict).
  - 출력 키: `job_meta`, `task_static_meta`(정적 유형/도메인/RAG/가치/복잡도/env/tags/entities), `static_summary`.
  - JSON-only, 코드블록 금지, 입력 복사 규칙 명시.
- **Stage 3-A – Workflow Struct (`prompts/workflow_struct.txt`)**
  - 입력 `job_meta`, `raw_job_desc`, `task_atoms`, `ivc_tasks`, `phase_summary`를 그대로 복사.
  - 허용 top-level 키: `workflow_name`, `workflow_summary`, `stages`, `streams`, `nodes`, `edges`, `entry_points`, `exit_points`, `notes`.
  - 노드/엣지 ID는 영문+숫자, entry/exit/hub 플래그를 분리해 반환.
- **Stage 3-B – Workflow Mermaid (`prompts/workflow_mermaid.txt`)**
  - 입력 `WorkflowPlan`을 그대로 사용해 노션 호환 Mermaid flowchart TD 코드 생성.
  - 허용 top-level 키: `workflow_name`, `mermaid_code`, `warnings`.
  - 코드블록 금지, mermaid_code만 포함된 단일 JSON을 요구.

## 버전/변경 관리
- 프롬프트 변경 시: 변경 요약을 `docs/iteration_log.md`에 기록(날짜, 이유, 영향).
- 프롬프트 캐시: 수정 후 Streamlit 재시작 또는 `load_prompt.cache_clear()`로 갱신.
- 모델 호환성: web_browsing이 필요한 프롬프트는 기본 `gemini-2.5-flash` 기준으로 작성.
