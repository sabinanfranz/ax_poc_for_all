# UX/UI 개요
> Last updated: 2025-12-03 (by AX Agent Factory Codex)

## 화면 구조
- Streamlit 단일 페이지(`ax_agent_factory/app.py`), `wide` 레이아웃. 상단 타이틀/캡션 아래에 Stage별 탭이 전개된다.
- 사이드바 입력(회사명/직무명/JD 직접 입력)과 세 개의 실행 버튼으로만 조작한다.
- 메인 영역은 구현된 Stage만 탭으로 노출한다(Stage 0→1→3; Stage 3은 UI상 2.1/2.2). 각 Stage 탭 내부는 공통 서브탭(Input, 결과, LLM 원문, LLM 파싱, 에러, 설명, I/O)으로 평평하게 배치된다.
- 하단 expander에서 `logs/app.log` tail을 바로 확인할 수 있어 실행 중 로그 디버깅이 가능하다.

## 사이드바 입력/실행 흐름
- 필수 입력: 회사명, 직무명. 선택 입력: `manual_jd_text`(직접 붙여넣은 JD 텍스트).
- 버튼
  - `0. Job Research 실행`: Stage 0만 강제 재실행(캐시 무시) 후 DB/세션 저장.
  - `0~1단계 실행 (Job Research → IVC)`: Stage 0 실행 후 Stage 1까지 연속 수행.
  - `0~1~2단계 실행 (Job Research → IVC → Workflow)`: Stage 0/1 실행 후 Workflow(2.1 Struct → 2.2 Mermaid)까지 연속 수행.
- 실행 시 Spinner와 성공/오류 메시지를 즉시 표시. 입력 값이 없으면 버튼을 눌러도 실행되지 않는다.
- `st.session_state`에 job_run, manual_jd_text, Stage별 결과를 보관해 탭 전환 시 상태가 유지된다. Stage 0 결과는 필요 시 DB에서 재조회한다.

## Stage 탭 구성(현재 구현)
- **0.1 Job Research Collect**: 입력 JSON(company/job/manual_jd_text), `raw_sources` 리스트 표시. LLM raw/정규화/에러 탭으로 웹 검색 응답을 그대로 확인.
- **0.2 Job Research Summarize**: 입력으로 0.1 `raw_sources`와 job_meta를 JSON으로 보여주고, 결과 탭에 `raw_job_desc` 텍스트 + `research_sources` 리스트를 분리 노출.
- **1-A Task Extractor**: Stage 0 `raw_job_desc`를 입력 JSON으로 보여주고 `task_atoms`만 결과 탭에 표시. 스텁일 때는 빈/단일 태스크 안내 메시지로 구분.
- **1-B Phase Classifier**: 입력 JSON에 `task_atoms` 재노출, 결과 탭에 `ivc_tasks`와 `phase_summary`를 병렬 표기. 에러 탭에서 LLM 파싱 오류 여부 확인.
- **2.1 Workflow Struct**: 입력에 job_meta + `ivc_tasks`/`task_atoms`/`phase_summary` JSON. 결과 탭에서 `workflow_name`, `stages`, `streams`, `nodes`, `edges`를 각각 하위 섹션으로 렌더링.
- **2.2 Workflow Mermaid**: 입력으로 2.1 결과 전체 JSON을 보여주고, 결과 탭에 `mermaid_code`(mermaid 코드 블록)와 `warnings`를 출력.
- 공통: LLM 원문/정규화/에러 탭은 스텁/캐시인 경우 안내 메시지를 표기해 데이터 유무를 명확히 한다. 설명/I/O 탭에 입력·출력 필드와 사용 모듈/프롬프트 경로를 요약한다.

## 디버깅/가드레일
- 모든 Stage 결과 객체에 `llm_raw_text`, `llm_cleaned_json`, `llm_error`를 부착해 동일한 탭 구조로 노출한다. JSON 파싱 실패 시 에러 탭에 문구가 그대로 표시된다.
- LLM 키 부재나 파싱 실패 시에도 내부 스텁으로 결과를 생성해 화면이 끊기지 않으며, 스텁 여부는 에러/원문 탭의 안내 문구로 알 수 있다.
- `logs/app.log` tail expander로 최근 로그를 즉시 확인 가능. 파일 접근 오류는 UI를 깨지 않도록 무시한다.

## 상태/저장
- Stage 0(Collect/Summarize) 결과는 SQLite(`data/ax_factory.db`)에 저장·조회한다. Stage 1/Workflow 결과는 세션 상태에만 존재한다.
- 버튼 실행 시 Stage 0은 항상 `force_rerun=True`로 새로 호출하며, 이후 Stage 1/Workflow를 순차적으로 이어간다.
