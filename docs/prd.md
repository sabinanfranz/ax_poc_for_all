# AX Agent Factory – PRD
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## 1. 제품 개요
- 목표: `회사명 + 직무명 (+ 선택적 JD 텍스트)` 입력만으로 **직무 리서치 → IVC 업무 원자화**를 자동화하고, 이후 DNA/Workflow/Agent/Prompt까지 확장 가능한 파이프라인을 갖춘다.
- 현재 범위(v0.1 PoC): **Stage 0 (Job Research) + Stage 1 (IVC Task Extractor → Phase Classifier)**만 동작. 나머지 Stage는 설계/스텁 상태.
- 사용성: Streamlit UI 단일 페이지, SQLite 캐시, 프롬프트 외부화, LLM 스텁 내장(키 없을 때도 흐름 유지).

## 2. 대상 사용자 & 주요 시나리오
- 사용자: 기획/HR/프로덕트 오너(비개발자) + 테크니컬 라이터/엔지니어.
- 시나리오
  - 회사/직무 입력 → Stage 0 실행 → Stage 1 실행 → UI에서 결과 확인/다운로드.
  - JD 텍스트를 수동 제공해도 되고, 미제공 시 웹 리서치로 수집.
  - LLM 키가 없을 때도 스텁으로 흐름/데모 가능.

## 3. Stage별 요구사항 (현재 구현 기준)
- **Stage 0: Job Research (구현)**
  - 입력: company_name, job_title, manual_jd_text(optional)
  - 처리: Stage 0.1 `infra/llm_client.call_job_research_collect`(web_search) → Stage 0.2 `call_job_research_summarize` → 파싱 실패 시 스텁.
  - 출력: `raw_job_desc`, `research_sources[]`, 디버그용 `_raw_text`/`llm_error`는 UI에서 표시.
  - 캐시: job_run_id 기준 SQLite 저장/조회.
- **Stage 1: IVC (구현)**
  - 입력: Stage 0 raw_job_desc + job_meta.
  - 1-A Task Extractor: `core/ivc/task_extractor.py` + `prompts/ivc_task_extractor.txt` → `task_atoms[]`.
  - 1-B Phase Classifier: `core/ivc/phase_classifier.py` + `prompts/ivc_phase_classifier.txt` → `ivc_tasks[]`, `phase_summary`.
  - 공통 규칙: LLM JSON 하나만 응답, 코드블록 금지, 스텁 fallback 제공.
  - 현재 상태: LLMClient.call은 미구현으로 기본 스텁 결과를 반환(테스트/데모용). 실제 모델 연결 시 LLMClient 확장 필요.
- **Stage 2~3 이후 (미구현/설계)**
  - Stage 2 DNA: Primitive/Domain/Mechanism 주석.
  - Stage 3 Workflow: Stage/Stream/Task 구조화 + Mermaid.
  - Stage 4~9 AX/Agent/Skill/Prompt/Runner: 설계만 남기고 구현 보류.

## 4. 범위·비범위
- 포함(In Scope, v0.1): Streamlit UI, PipelineManager 오케스트레이션, Stage 0/1 로직, SQLite 캐시, 프롬프트 파일 관리, 기본 로깅, pytest 기반 단위 테스트.
- 제외(Out of Scope, 당분간):
  - 멀티 모델 비교/라우팅, 대규모 배치 파이프라인, 에이전트 실행/검증 자동화.
  - 프로덕션 보안/인증, 관측성(메트릭/트레이싱), UI 다국어/접근성 완비.
  - Stage 2~9 실제 로직, Runner 및 평가 파이프라인.

## 5. 비기능 요구사항 (PoC 기준)
- 신뢰성: LLM 실패 시 스텁으로 중단 없이 이어갈 것.
- 가시성: logs/app.log 로테이션, UI에서 LLM raw/error 노출.
- 재현성: 프롬프트는 파일로 분리, 테스트에서 DB/LLM을 모킹 가능해야 함.
- 설정: 환경변수 `GOOGLE_API_KEY`(없으면 스텁), `GEMINI_MODEL`(기본 gemini-2.5-flash), `AX_DB_PATH`(기본 data/ax_factory.db).

## 6. 성공 지표 (PoC 관점)
- 기능: Stage 0/1 버튼 실행 시 UI에서 결과/원문 확인 가능.
- 안정성: LLM 키 부재/JSON 파싱 실패 시에도 예외 없이 스텁으로 반환.
- 문서화: docs/*.md와 코드가 1:1로 대응되고, 비개발자도 실행 경로를 이해 가능.

## 7. 로드맵(요약)
- 단기(다음 스프린트): Stage 1 결과 지속화(DB), LLMClient.call 실제 구현, JSON 검증 강화/리트라이.
- 중기: Stage 2 DNA, Stage 3 Workflow 스펙/모델/프롬프트 확정 및 구현.
- 장기: Stage 4~9(AX/Agent/Skill/Prompt/Runner) 구현, 멀티 모델/평가/관측성/배포 자동화.
