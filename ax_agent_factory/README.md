# AX Agent Factory – PoC

Streamlit 기반 내부 툴로 0~9단계 파이프라인을 순차 실행/확인하는 PoC입니다. 현재는 Stage 0 (Job Research), Stage 1 (IVC Task Extractor/Phase Classifier), Stage 3 (Workflow Struct → Mermaid; UI에서는 2.1/2.2 탭)까지 동작하며, LLM 미연결 시 스텁 fallback이 내장되어 있습니다. Stage 메타데이터의 `implemented` 플래그에 따라 UI 탭이 노출됩니다.

## 구조

```
ax_agent_factory/
  app.py                 # Streamlit 진입점(UI 탭/버튼/로그)
  core/
    pipeline_manager.py  # Stage 실행/캐싱/DB 연동
    research/            # Stage 0: 0.1 collect → 0.2 summarize
    ivc/                 # Stage 1: Task Extractor/Phase Classifier + 파이프라인
    workflow.py          # Stage 3: Workflow Struct(2.1) → Mermaid(2.2)
    dna.py               # Stage 2 stub
    schemas/common.py    # IVC 입력/출력 스키마
    schemas/workflow.py  # Workflow/Mermaid 스키마
  infra/
    llm_client.py        # Gemini 호출/파서/스텁 + LLM 로그 기록
    prompts.py           # 프롬프트 로더(LRU 캐시)
    db.py                # SQLite CRUD(job_runs, job_research_results 등)
    logging_config.py    # 콘솔/파일 로깅 설정
  models/
    stages.py            # Stage 메타데이터 정의
    job_run.py           # JobRun / JobResearchResult 모델
    llm_log.py           # LLM 호출 로그 모델
  prompts/
    job_research_collect.txt
    job_research_summarize.txt
    ivc_task_extractor.txt
    ivc_phase_classifier.txt
    workflow_struct.txt
    workflow_mermaid.txt
  tests/                 # pytest 스위트(Stage 0/1/3, LLM 로그)
```

## 설치 및 실행

```bash
pip install -r requirements.txt
export AX_DB_PATH=./data/ax_factory.db   # 선택, 기본 경로는 data/ax_factory.db
export GOOGLE_API_KEY=your-gemini-api-key # LLM 연결 시 필요 (없으면 스텁 동작)
export GEMINI_MODEL=gemini-2.5-flash      # 선택, 기본 gemini-2.5-flash (web_search 지원)
streamlit run ax_agent_factory/app.py
```

## 테스트

```bash
pytest ax_agent_factory/tests
```

## Stage 확장 가이드

1. `models/stages.py`에서 해당 Stage의 `implemented=True`로 변경.
2. `core/<stage>.py` 또는 `core/<stage>/`에 로직 구현, `core/pipeline_manager.py`에 `run_stage_X_*` 구현.
3. `app.py`에 렌더링 함수 추가 후 탭에 연결(UI 디버그 필드 포함).
4. 필요한 스키마/DB 컬럼을 PRD 정의에 맞춰 확장.
