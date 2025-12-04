# AX Agent Factory – PRD
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 1. 제품 개요
- 목표: `회사명 + 직무명 (+ 선택적 JD 텍스트)` 입력만으로 **직무 리서치 → IVC 업무 원자화 → 정적 분류 → 워크플로우 구조화/머메이드**까지 자동화하고, 이후 DNA/Agent/Prompt까지 확장 가능한 파이프라인을 갖춘다.
- 현재 범위(v0.2 PoC): **Stage 0 (Job Research 0.1/0.2) + Stage 1 (IVC 1.1/1.2 + Static 1.3) + Stage 2 (Workflow 2.1/2.2)**가 동작한다. Stage 3~9는 설계 상태.
- 사용성: Streamlit UI 단일 페이지, “다음 단계 실행” 버튼으로 순차 진행, SQLite 캐시, 프롬프트 외부화, LLM 스텁 내장(키 없을 때도 흐름 유지).

## 2. 대상 사용자 & 주요 시나리오
- 사용자: 기획/HR/프로덕트 오너(비개발자) + 테크니컬 라이터/엔지니어.
- 시나리오
  - 회사/직무 입력 → Stage 0 실행 → Stage 1 실행 → UI에서 결과 확인/다운로드.
  - JD 텍스트를 수동 제공해도 되고, 미제공 시 웹 리서치로 수집.
  - LLM 키가 없을 때도 스텁으로 흐름/데모 가능.

## 3. Stage별 요구사항 (현재 구현 기준)
- **Stage 0: Job Research (0.1/0.2 구현)**
  - 입력: company_name, job_title, manual_jd_text(optional)
  - 처리: Stage 0.1 `infra/llm_client.call_job_research_collect`(web_search) → Stage 0.2 `call_job_research_summarize` → 파싱 실패 시 스텁.
  - 출력: `raw_job_desc`, `research_sources[]`, 디버그용 `_raw_text`/`llm_error`는 UI에서 표시.
  - 캐시: job_run_id 기준 SQLite 저장/조회(legacy 컬럼 호환 포함).
- **Stage 1: IVC + Static (구현)**
  - 입력: Stage 0 raw_job_desc + job_meta.
  - 1.1 Task Extractor: `call_task_extractor` → `task_atoms[]` → DB `job_tasks` task_* 컬럼 저장.
  - 1.2 Phase Classifier: `call_phase_classifier` → `ivc_tasks[]`, `phase_summary` → DB `job_tasks` ivc_* 컬럼 업데이트.
  - 1.3 Static Task Classifier: `call_static_task_classifier` → `task_static_meta[]`, `static_summary` → DB `job_tasks` static_* 컬럼 업데이트.
  - 공통 규칙: LLM JSON 하나만 응답, 코드블록 금지, sanitizer/파서로 경미한 오류 흡수, 실패 시 스텁 fallback.
- **Stage 2: Workflow (구현, UI 2.1/2.2)**
  - 입력: PhaseClassificationResult(1.2) 결과 dict.
  - 2.1 Workflow Struct: `call_workflow_struct` → `WorkflowPlan` → DB `job_tasks` stage/stream/entry/exit/hub + `job_task_edges`.
  - 2.2 Workflow Mermaid: `call_workflow_mermaid` → `MermaidDiagram`.
  - 공통 규칙: JSON-only 응답, sanitizer로 경미한 오류 흡수, 실패/키 부재 시 스텁.
- **Stage 3~9 이후 (미구현/설계)**: AX/Agent/Skill/Prompt/Runner 등은 설계만 남기고 구현 보류.

## 4. 범위·비범위
- 포함(In Scope, v0.2): Streamlit UI(“다음 단계 실행” 버튼/탭), PipelineManager 오케스트레이션, Stage 0/1.1/1.2/1.3/2.1/2.2 로직, SQLite 캐시(Stage 0 + job_tasks/job_task_edges), 프롬프트 관리, 기본 로깅, pytest 기반 단위 테스트.
- 제외(Out of Scope, 당분간):
  - 멀티 모델 비교/라우팅, 대규모 배치 파이프라인, 에이전트 실행/검증 자동화.
  - 프로덕션 보안/인증, 관측성(메트릭/트레이싱), UI 다국어/접근성 완비.
  - Stage 3~9 실제 로직, Runner 및 평가 파이프라인.

## 5. 비기능 요구사항 (PoC 기준)
- 신뢰성: LLM 실패 시 스텁으로 중단 없이 이어갈 것.
- 가시성: logs/app.log 로테이션, UI에서 LLM raw/error 노출.
- 재현성: 프롬프트는 파일로 분리, 테스트에서 DB/LLM을 모킹 가능해야 함.
- 설정: 환경변수 `GOOGLE_API_KEY`(없으면 스텁), `GEMINI_MODEL`(기본 gemini-2.5-flash), `AX_DB_PATH`(기본 data/ax_factory.db).

## 6. 성공 지표 (PoC 관점)
- 기능: “다음 단계 실행” 4번으로 0.2 → 1.2 → 1.3 → 2.2까지 자연스럽게 도달, 각 탭에서 결과/원문 확인 가능.
- 안정성: LLM 키 부재/JSON 파싱 실패 시에도 예외 없이 스텁으로 반환, DB NOT NULL 제약 없이 저장.
- 문서화: docs/*.md와 코드가 1:1로 대응되고, 비개발자도 실행 경로를 이해 가능.

## 7. 로드맵(요약)
- 단기(다음 스프린트): Static/Workflow 결과 UI 보강, Stage 0/1/2 캐시 재사용 옵션, max_tokens/모델 설정 UI화.
- 중기: Stage 2 DNA 스키마·프롬프트 확정 후 최초 구현, Workflow/IVC 간 재실행 캐시/리트라이 도입.
- 장기: Stage 4~9(AX/Agent/Skill/Prompt/Runner) 구현, 멀티 모델/평가/관측성/배포 자동화.
