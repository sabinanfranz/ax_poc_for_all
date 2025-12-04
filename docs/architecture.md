# AX Agent Factory – Architecture
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 1. 시스템 개요 (레이어)
- **UI**: `app.py` (Streamlit). 회사/직무 입력 → “다음 단계 실행”/개별 버튼 → Stage별 탭(Input/Result/LLM Raw/Parse/Error/설명/I/O) 표시.
- **Core**: 비즈니스 로직과 파이프라인.
  - `core/pipeline_manager.py`: Stage 실행/캐시/순차 실행(`run_pipeline_until_stage`) 오케스트레이션.
  - `core/research/*`: Stage 0 Job Research (0.1 Collect → 0.2 Summarize).
  - `core/ivc/*`: Stage 1 IVC(Task Extractor 1.1, Phase Classifier 1.2, pipeline) + Static Classifier 1.3.
  - `core/workflow.py`: Stage 2 Workflow Struct(2.1) → Mermaid(2.2) 파이프라인(LLM/스텁).
  - `core/dna.py`: Stage 2 DNA 스텁(미사용).
- **Infra**: 공통 유틸.
  - `infra/db.py`: SQLite CRUD(job_runs, job_research_results, job_research_collect_results, job_tasks, job_task_edges), 경로 `AX_DB_PATH` 기본 `data/ax_factory.db`(legacy 컬럼 호환).
  - `infra/llm_client.py`: Gemini web_browsing 호출 + JSON 파서/스텁. Stage 0/1/1.3/2용 `call_job_research_*`, `call_task_extractor`, `call_phase_classifier`, `call_static_task_classifier`, `call_workflow_struct`, `call_workflow_mermaid` 헬퍼 제공(키 없을 때 스텁, max_tokens 기본 81920).
  - `infra/prompts.py`: 프롬프트 파일 로더(LRU 캐시).
  - `infra/logging_config.py`: 콘솔+회전 파일 로그 초기화.
- **Models/Schemas**:
  - `models/job_run.py`: JobRun(확장 필드 포함), JobResearchResult, JobResearchCollectResult dataclass.
  - `models/stages.py`: Stage 메타(PIPELINE_STAGES, ui_group/ui_step/ui_label/tab_title).
  - `core/schemas/common.py`: JobMeta/JobInput/IVCAtomicTask/TaskExtractionResult/IVCTask/PhaseSummary/PhaseClassificationResult/TaskStaticMeta/StaticClassificationResult.
  - `core/schemas/workflow.py`: WorkflowPlan, MermaidDiagram 등 Stage 2 결과 스키마.
- **Prompts**: `prompts/*.txt`로 Stage별 프롬프트 분리(collect/summarize/task_extractor/phase_classifier/static_task_classifier/workflow_struct/workflow_mermaid).

## 2. PipelineManager 역할
- “Stage 공장장”: 버튼 입력 시 JobRun을 만들고 Stage 순서대로 실행.
- **캐싱/순차 실행**: Stage 0 결과가 DB에 있으면 재사용(단, force_rerun=True 시 새 호출). `run_pipeline_until_stage`가 `PIPELINE_STAGES`(ui_group/ui_step 순) 기준으로 0.2→1.2→1.3→2.2 순차 실행.
- **확장성**: `PIPELINE_STAGES`의 `run_fn_name`을 호출하는 구조로 Stage 추가 시 확장 용이.

- **Stage 0: Job Research**
  - 입력: company_name, job_title, manual_jd_text(optional).
  - 0.1 Collect: `llm_client.call_job_research_collect`(web_search, `job_research_collect.txt`) → raw_sources 저장.
  - 0.2 Summarize: `llm_client.call_job_research_summarize`(`job_research_summarize.txt`) → raw_job_desc, research_sources.
  - 출력: JobResearchCollectResult(raw_sources), JobResearchResult(raw_job_desc, research_sources) + UI용 llm_raw_text/llm_error.
  - 영속화: SQLite에 저장/조회(job_research_collect_results, job_research_results, legacy 컬럼 호환).
- **Stage 1: IVC + Static**
  - 입력: JobInput(job_meta + raw_job_desc).
  - 1.1 Task Extractor: `IVCTaskExtractor.run` → `task_atoms[]` → DB `job_tasks` task_* 저장.
  - 1.2 Phase Classifier: `IVCPhaseClassifier.run` → `ivc_tasks[]`, `phase_summary` → DB `job_tasks` ivc_* 업데이트.
  - 1.3 Static Task Classifier: `StaticTaskClassifier.run` → `task_static_meta[]`, `static_summary` → DB `job_tasks` static_* 업데이트.
  - 오케스트레이션: `core/ivc/pipeline.py` 또는 `PipelineManager.run_pipeline_until_stage`.
- **Stage 2: Workflow (UI 2.1/2.2)**
  - 입력: PhaseClassificationResult dict(raw_job_desc, ivc_tasks, task_atoms, phase_summary, job_meta).
  - 2.1 Workflow Struct: `core/workflow.py::WorkflowStructPlanner.run` → `call_workflow_struct` → `WorkflowPlan` → DB `job_tasks` stage/stream/entry/exit/hub, `job_task_edges`.
  - 2.2 Workflow Mermaid: `WorkflowMermaidRenderer.run` → `call_workflow_mermaid` → `MermaidDiagram`.
  - 영속화: job_tasks/job_task_edges(노드/엣지). LLM 실패/키 부재 시 스텁으로 노드/엣지/머메이드 코드 생성.

## 4. LLM/프롬프트/로깅
- **LLM**: Gemini web_browsing(google-genai). 기본 `gemini-2.5-flash`(env `GEMINI_MODEL`). 키/SDK 없으면 스텁. Stage 1/2는 `call_task_extractor` / `call_phase_classifier` / `call_static_task_classifier` / `call_workflow_struct` / `call_workflow_mermaid` 헬퍼로 동일한 파서/스텁/로그 정책을 공유한다. 기본 `max_tokens=81920`.
- **프롬프트**: `prompts/job_research_collect.txt`, `prompts/job_research_summarize.txt`, `prompts/ivc_task_extractor.txt`, `prompts/ivc_phase_classifier.txt`, `prompts/static_task_classifier.txt`, `prompts/workflow_struct.txt`, `prompts/workflow_mermaid.txt`. JSON-only 규칙, 코드블록 금지, one-shot 예시 포함.
- **로깅**: `infra/logging_config.setup_logging`이 콘솔/파일 핸들러 구성(중복 방지 플래그 사용). UI에서 `logs/app.log` tail을 expander로 노출.

## 5. 테스트 및 관측 포인트
- 테스트: `ax_agent_factory/tests`에서 DB 캐시, Stage 0 결과 저장, Stage 1/1.3/2 파이프라인 파싱/스텁/DB 영속 동작 검증.
- 관측: Stage별 logger 사용, UI 탭에서 LLM raw/error 확인. 향후 JSON 밸리데이션 강화/메트릭 추가 예정.
