# Code Description
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## UI
- `ax_agent_factory/app.py`: Streamlit 진입점. 사이드바 입력/버튼(0/1/1.3/2, “다음 단계 실행”) → `PipelineManager` 호출 → Stage별 탭 렌더링(Stage 0.1/0.2, 1.1/1.2/1.3, 2.1/2.2) 및 로그 expander 출력.

## Core – Pipeline & Research
- `core/pipeline_manager.py`: JobRun 생성(`create_or_get_job_run`) 및 Stage 실행기(`run_stage_0_*`, `run_stage_1_*`, `run_stage_2_*`, `run_pipeline_until_stage`). Stage 0는 DB 캐시 후 재사용, Stage 1/2는 입력 검증 후 하위 파이프라인 호출 및 job_tasks/job_task_edges 업데이트.
- `core/research/pipeline.py`: Stage 0 전체 흐름(0.1 결과 DB 캐시 → 0.2 실행) 오케스트레이션.
- `core/research/collector.py`: `run_job_research_collect`가 `call_job_research_collect` 호출 → `JobResearchCollectResult` 생성/DB 저장 + LLM 디버그 필드 부착.
- `core/research/synthesizer.py`: `run_job_research_summarize`가 0.1 결과 기반 `call_job_research_summarize` 호출 → `JobResearchResult` 저장 + 디버그 필드 부착.

## Core – IVC
- `core/ivc/pipeline.py`: `run_ivc_pipeline`가 Task Extractor → Phase Classifier 순차 실행 후 `task_atoms`를 최종 결과에 재첨부.
- `core/ivc/task_extractor.py`: `IVCTaskExtractor.run`이 `call_task_extractor` → `parse_task_extraction_dict`로 Pydantic 검증, 실패 시 `_stub_result` 제공. `build_prompt`로 `{input_json}` 템플릿 구성.
- `core/ivc/phase_classifier.py`: `IVCPhaseClassifier.run`이 `call_phase_classifier` → `parse_phase_classification_dict`, 실패 시 `_stub_result`로 모든 태스크를 SENSE에 매핑. `build_prompt` 제공.
- `core/ivc/static_classifier.py`: `StaticTaskClassifier.run`이 `call_static_task_classifier` → `StaticClassificationResult`, 실패 시 스텁. job_tasks static_* 컬럼 업데이트.

## Core – Workflow & DNA
- `core/workflow.py`: Stage 2 파이프라인. `WorkflowStructPlanner.run`이 `call_workflow_struct`로 `WorkflowPlan`을 받고 디버그 필드를 복사 후 job_tasks/job_task_edges를 업데이트. `WorkflowMermaidRenderer.run`이 `call_workflow_mermaid`로 `MermaidDiagram` 생성. `run_workflow`가 2.1 → 2.2 순서로 호출(스텁은 LLM 헬퍼 내부에서 생성).
- `core/dna.py`: DNA 스텁(`run_dna` NotImplemented).

## Schemas
- `core/schemas/common.py`: IVC 입력/출력 Pydantic 모델(JobMeta, JobInput, IVCAtomicTask, TaskExtractionResult, IVCTaskListInput, IVCTask, PhaseSummary, PhaseClassificationResult).
- `core/schemas/workflow.py`: WorkflowPlan/WorkflowStage/WorkflowStream/WorkflowNode/WorkflowEdge 및 MermaidDiagram 모델(LLM 디버그 필드 포함).

## Infra
- `infra/db.py`: SQLite 경로 설정(`set_db_path`), 테이블 보장, CRUD(`create_or_get_job_run`, Stage 0 저장/조회, job_tasks/job_task_edges upsert), LLM 로그 저장/조회. legacy 컬럼(raw_sources/research_sources) 호환.
- `infra/llm_client.py`: Stage별 Gemini 호출/파서/스텁. `call_job_research_collect|summarize`, `call_task_extractor`, `call_phase_classifier`, `call_static_task_classifier`, `call_workflow_struct`, `call_workflow_mermaid`가 공통 sanitizer/JSON 정규화(`_extract_json_from_text`, `_parse_json_candidates`)와 스텁(`_stub_*`), 기본 `max_tokens=81920`을 사용. `_safe_save_llm_log`로 LLM 호출 메타 저장, `InvalidLLMJsonError` 정의.
- `infra/prompts.py`: `load_prompt`로 프롬프트 파일을 LRU 캐시 후 로드.
- `infra/logging_config.py`: `setup_logging`이 콘솔/회전 파일 핸들러 설정(중복 방지 플래그).

## Models
- `models/job_run.py`: JobRun, JobResearchResult, JobResearchCollectResult dataclass 정의.
- `models/llm_log.py`: LLMCallLog dataclass 정의(토큰/레이턴시/에러 메타 포함).
- `models/stages.py`: StageMeta/PIPELINE_STAGES 정의(implemented 플래그 기반 UI 탭 노출, Stage 3 Workflow는 implemented=True).

## Prompts
- `prompts/job_research_collect.txt`, `job_research_summarize.txt`: Stage 0.1/0.2 입력을 받아 JSON-only 결과 생성.
- `prompts/ivc_task_extractor.txt`, `ivc_phase_classifier.txt`: Stage 1 입력 스키마 명시 및 JSON-only 출력 규칙.
- `prompts/workflow_struct.txt`, `workflow_mermaid.txt`: Stage 3-A/3-B 워크플로우 구조화 및 Mermaid 렌더링 규칙.
- `prompts/job_research.txt`: 초기 단일 프롬프트(현재 파이프라인에서는 사용하지 않음).

## Tests
- `tests/test_research_stage.py`: Stage 0 collect/summarize 흐름, DB 저장, 디버그 필드 확인.
- `tests/test_pipeline_manager.py`: Stage 0 캐시 재사용, Stage 1 입력 검증.
- `tests/test_ivc_task_extractor.py` / `test_ivc_phase_classifier.py` / `test_static_classifier_stage.py`: sanitizer/파싱/LLM 디버그 필드/스텁 검증.
- `tests/test_ivc_pipeline.py`: Task Extractor → Phase Classifier 연계 및 스텁/DB 동작.
- `tests/test_workflow_struct_mermaid.py`: Workflow Struct/ Mermaid 파서 스텁/정상 JSON 검증, DB 반영 확인.
- `tests/test_llm_call_logging.py`: LLM 호출 로그 저장, 토큰 메타 추출 검증.
- `tests/test_db_job_tasks.py`: job_tasks/job_task_edges upsert/end-to-end 업데이트 검증.
- `tests/test_pipeline_next_stage.py`: `get_next_label`/`run_pipeline_until_stage` 순차 실행 검증.
