# File Structure
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

```
ax_agent_factory/
  app.py                      # Streamlit UI entrypoint (Stage 0/1 실행 탭)
  core/
    pipeline_manager.py       # Stage 실행/캐시 오케스트레이터
    research/                 # Stage 0 Job Research (0.1 Collect → 0.2 Summarize)
      __init__.py
      collector.py            # Stage 0.1 Web Research Collector
      synthesizer.py          # Stage 0.2 Task-Oriented Synthesizer
      pipeline.py             # Stage 0 전체 파이프라인
    ivc/
      task_extractor.py       # Stage 1-A: IVC Task Extractor (LLM JSON→task_atoms, 스텁 지원)
      phase_classifier.py     # Stage 1-B: IVC Phase Classifier (LLM JSON→ivc_tasks, 스텁 지원)
      pipeline.py             # Task Extractor → Phase Classifier 연결
    dna.py                    # Stage 2 DNA 스텁
    workflow.py               # Stage 3 Workflow 스텁
    schemas/common.py         # IVC 입력/출력 Pydantic 모델
  infra/
    db.py                     # SQLite CRUD(job_runs, job_research_results, job_research_collect_results), AX_DB_PATH로 경로 설정
    llm_client.py             # Gemini web_browsing 호출기 + JSON 파서/스텁
    prompts.py                # 프롬프트 로더(LRU 캐시)
    logging_config.py         # 콘솔+회전 파일 로깅 설정
  models/
    job_run.py                # JobRun, JobResearchResult, JobResearchCollectResult dataclass
    stages.py                 # Stage 메타데이터(PIPELINE_STAGES)
  prompts/
    job_research_collect.txt  # Stage 0.1 프롬프트 (web_search, raw_sources JSON)
    job_research_summarize.txt# Stage 0.2 프롬프트 (raw_job_desc + research_sources JSON)
    ivc_task_extractor.txt    # Stage 1-A 프롬프트 (one-shot + JSON 스키마)
    ivc_phase_classifier.txt  # Stage 1-B 프롬프트 (one-shot + JSON 스키마)
  tests/                      # pytest 단위 테스트 (DB 캐시, IVC 파이프라인, 스텁 동작)
data/                         # 기본 SQLite 경로(data/ax_factory.db), AX_DB_PATH로 변경 가능
docs/                         # 문서 세트(PRD, 아키텍처, 로직 플로우, 스키마 등)
logs/                         # 로그 출력 디렉터리 (logging_config가 생성)
prompts_reference/            # 참고용 기존 프롬프트 보관
requirements.txt              # 의존성 목록(streamlit, pydantic, pytest, google-genai 등)
```

## Quick Roles
- UI: `app.py`가 사이드바 입력 → Stage 0/1 실행 버튼 → 결과/LLM 원문 탭 제공.
- 오케스트레이션: `core/pipeline_manager.py`가 Stage별 실행/캐시/검증 담당.
- LLM/프롬프트: `infra/llm_client.py` + `prompts/*.txt` + `infra/prompts.py` 로더.
- 영속화: SQLite(`infra/db.py`), job_runs/job_research_results 테이블.
- 테스트: `ax_agent_factory/tests`에서 LLM 모킹, 캐시, 파이프라인 파싱/스텁 검증.
