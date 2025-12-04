# Documentation Operations Guide
> Last updated: 2025-12-04 (by AX Agent Factory Codex)
> 목적: AX Agent Factory 레포의 모든 주요 .md를 항상 최신 상태로 유지하기 위한 운영 지침. 대상: 문서/코드 기여자 전원. 연결: Stage–Prompt–Schema–DB–UI 5각형, `iteration_log.md` 기록.

## 1. 공통 운영 원칙

1. **단일 진실 계층**
   1) 실제 코드/스키마 → 2) 프롬프트(`prompts/*.txt`) → 3) 스키마/DB 문서(`schema.md`, `database_tables.md`, `database_and_table.md`) → 4) 아키텍처/로직/PRD(`architecture.md`, `logic_flow.md`, `prd.md`) → 5) 기타 가이드. 문서를 고치기 전에 항상 1→5 순서로 실체를 확인한다.
2. **5각형 동기화 (Stage–Prompt–Schema–DB–UI)**
   - Stage 정의: PRD + `logic_flow.md` + `stage_runner.md`
   - Prompt: `prompts/*.txt`, `prompt_guidelines.md`
   - Schema: `core/schemas/*.py`, `schema.md`
   - DB: `infra/db.py`, `database_tables.md`, `database_and_table.md`
   - UI: `app.py`, `uxui.md`
   - 어느 한 곳을 바꾸면 연결된 문서를 함께 반영한다.
3. **모든 md 상단 규칙**
   - `# 제목` + `> Last updated: YYYY-MM-DD (by XXX)`
   - 문서 목적/대상/연결 Stage·코드를 3~4줄 요약
   - 마이너 수정이 아니면 `iteration_log.md`에 한 줄 추가
4. **변경 전후 공통 체크리스트**
   - [ ] 관련 Stage 및 입출력 스키마 확인 (`schema.md`, `logic_flow.md`)
   - [ ] Pydantic 모델·DB 컬럼 존재 확인 (`core/schemas/*.py`, `database_tables.md`)
   - [ ] 프롬프트 키 일치 확인 (`prompt_guidelines.md`, 각 `prompts/*.txt`)
   - [ ] UI 버튼/탭/세션 키 변화 확인 (`uxui.md`, `usage_guide.md`)
   - [ ] `progress.md`/`iteration_log.md` 변경 요약 반영
5. **Align Checker(선택)**
   - 스키마–프롬프트 정합성은 `agent_schema_prompt_align_checker.md`를 기준으로 자동 점검
   - 결과는 `align_check_result_*.md`에 축적; 새 Stage/프롬프트 후 갱신

## 2. 공통 “최신화” 절차 (순서)

1. 코드/DB 변경 수집: `core/`, `infra/db.py`, `models/`, `prompts/`
2. Stage 흐름·입출력 재확인: `logic_flow.md`, `schema.md`, 프롬프트
3. DB 매핑 점검: `job_tasks`, `job_task_edges`, `job_research_*` 등 (`database_tables.md`, `database_and_table.md`)
4. UI/UX 경로 업데이트: 버튼/탭/세션 키/로그 (`uxui.md`, `usage_guide.md`)
5. 문서별 반영: 아래 per-file 가이드 활용
6. 기록: `progress.md`, `iteration_log.md`에 변경 묶음 기록

## 3. MD 파일별 업데이트 가이드 (체크용)

- **README.md**: PRD 범위와 일치, `usage_guide.md` 커맨드/환경변수 일치, Stage 구현 상태 최신화.
- **prd.md / AX_PRD_V2_FOR_CODEX.md**: Stage 0~2 로직/에러 처리/범위 정합, In/Out scope 최신화, AX 설계·구현 플래그 반영.
- **architecture.md**: 레이어/모듈 반영, PipelineManager 흐름이 `logic_flow.md`와 일치, AX 레이어 포함 여부.
- **file_structure.md**: 디렉터리/파일 트리 최신화, 새 모듈/폴더 추가 시 반영.
- **logic_flow.md**: 실행 순서·입출력 표·Mermaid가 코드/`PipelineManager`와 일치, 신규 Stage 반영.
- **schema.md**: Pydantic·DB 컬럼·프롬프트 top-level 키와 필드/타입 정합, AX 스키마 갱신.
- **database_tables.md**: `infra/db.py::_ensure_tables`와 컬럼/타입 일치, 컬럼 Stage 매핑 최신.
- **database_and_table.md**: Stage↔DB↔UI 매핑 정합, UI가 쓰는 필드 누락 여부, AX 테이블 설계 반영.
- **code_description.md**: 신규 모듈/러너 요약, Stage/LLM/DB 유틸 설명을 `logic_flow.md`와 맞춤.
- **usage_guide.md**: 설치/실행/테스트/환경변수 안내가 실제와 일치, 버튼 동작이 `uxui.md`와 동일.
- **troubleshooting.md**: 신규 빈발 에러 패턴·해결책 추가, 코드/파서 동작과 정합.
- **stage_runner.md**: 새 Stage에도 공통 라이프사이클 적용 여부, 디버그 필드 처리 규칙 일치.
- **parsing_guide.md**: 파서/샌드박스/스텁 정책이 코드와 일치, Stage별 파싱 플로우 정합.
- **prompt_guidelines.md**: Stage top-level 키 목록 정합, 신규 Stage 먼저 정의, llm_* 금지 강조.
- **gemini_models.md**: 실제 모델 기본값/사용 방식/대체 옵션·체크리스트 최신화.
- **uxui.md**: 사이드바 버튼/Stage 순서, 탭별 노출 필드, AX 버튼/DB 쓰기 요약 정합.
- **progress.md**: Stage 상태/최근 업데이트가 `iteration_log.md`와 모순 없도록 유지.
- **iteration_log.md**: 의미 있는 변경마다 한 줄 추가(날짜/내용/이유/영향), Last updated와 간극 없게 관리.
- **Docs Index (docs/README.md)**: 새 md 추가/삭제 시 목록·설명 갱신.
- **agent_schema_prompt_align_checker.md / align_check_result_*.md**: Align 스키마·샘플 결과 최신화.
- **versions/prd_v*.md**: 과거 PRD는 수정 금지, 새 메이저 변경 시 새 버전 생성·요약.

## 4. 정리용 미니 체크리스트

1) 코드/스키마/DB/프롬프트/UI 변경 사항 정리  
2) `schema.md`, `logic_flow.md`, `database_tables.md`, `prompt_guidelines.md`, `uxui.md` 우선 동기화  
3) `architecture.md`, `file_structure.md`, `code_description.md`, `usage_guide.md`, `troubleshooting.md` 갱신  
4) `prd.md`, `progress.md`, `iteration_log.md`, Docs Index, Align 문서 정리  
5) 모든 문서 Last updated 갱신 후 새 스프린트 시작
