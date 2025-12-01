# AX Agent Factory – PoC

Streamlit 기반 내부 툴로 0~9단계 파이프라인을 순차 실행/확인하는 PoC입니다. 현재는 Stage 0 (Job Research)와 Stage 1 (IVC Task Extractor/Phase Classifier; LLM 미연결 시 스텁 fallback)을 포함하며, Stage 메타데이터의 `implemented` 플래그만 켜면 UI 탭이 자동으로 노출되도록 설계되었습니다.
루트에 기존 scaffold(`/app`, `/core`, `/infra` 등)가 남아 있지만, **실제 실행/개발은 `ax_agent_factory/` 패키지를 기준으로 합니다.**

## 구조

```
ax_agent_factory/
  app.py                 # Streamlit 진입점
  core/
    pipeline_manager.py  # Stage 실행/캐싱/DB 연동
    research.py          # Stage 0 Job Research 비즈니스 로직
    ivc.py               # Stage 1 stub wrapper (현재 파이프라인에서 직접 사용하지 않음)
    ivc/                 # IVC Task Extractor/Phase Classifier + 파이프라인
  dna.py               # Stage 2 stub
  workflow.py          # Stage 3 stub
  infra/
    llm_client.py        # Gemini 호출 stub
    prompts.py           # 프롬프트 로더
    db.py                # SQLite 간단 CRUD
  models/
    stages.py            # Stage 메타데이터 정의
    job_run.py           # JobRun / JobResearchResult 모델
  prompts/
    ivc_task_extractor.txt
    ivc_phase_classifier.txt
  tests/
    test_research_stage.py
    test_pipeline_manager.py
    test_ivc_pipeline.py
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

1. `models/stages.py`에서 해당 Stage의 `implemented=True`로 변경
2. `core/<stage>.py` 또는 `core/<stage>/`에 로직 구현, `core/pipeline_manager.py`에 `run_stage_X_*` 구현
3. `app.py`에 렌더링 함수 추가 후 탭에 연결
4. 필요한 스키마/DB 컬럼을 PRD 정의에 맞춰 확장
