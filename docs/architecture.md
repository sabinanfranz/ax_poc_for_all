# AX Agent Factory – Architecture
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## 1. 시스템 개요 (레이어)
- **UI**: `app.py` (Streamlit). 회사/직무 입력 → Stage 0/1 실행 버튼 → 결과/LLM 원문 탭 표시.
- **Core**: 비즈니스 로직과 파이프라인.
  - `core/pipeline_manager.py`: Stage 실행/캐시 오케스트레이션.
  - `core/research/*`: Stage 0 Job Research (0.1 Collect → 0.2 Summarize).
  - `core/ivc/*`: Stage 1 IVC(Task Extractor, Phase Classifier, pipeline).
  - `core/dna.py`, `core/workflow.py`: Stage 2/3 스텁.
- **Infra**: 공통 유틸.
  - `infra/db.py`: SQLite CRUD(job_runs, job_research_results, job_research_collect_results), 경로 `AX_DB_PATH` 기본 `data/ax_factory.db`.
  - `infra/llm_client.py`: Gemini web_browsing 호출 + JSON 파싱/스텁. Stage 0/1용 `call_job_research_*`, `call_task_extractor`, `call_phase_classifier` 헬퍼를 제공(키 없을 때 스텁).
  - `infra/prompts.py`: 프롬프트 파일 로더(LRU 캐시).
  - `infra/logging_config.py`: 콘솔+회전 파일 로그 초기화.
- **Models/Schemas**:
  - `models/job_run.py`: JobRun, JobResearchResult, JobResearchCollectResult dataclass.
  - `models/stages.py`: Stage 메타(PIPELINE_STAGES).
  - `core/schemas/common.py`: IVC 입력/출력 Pydantic 모델(JobMeta, JobInput, IVCAtomicTask, IVCTask, PhaseSummary 등).
- **Prompts**: `prompts/*.txt`로 Stage별 프롬프트 분리.

## 2. PipelineManager 역할
- “Stage 공장장”: 버튼 입력 시 JobRun을 만들고 Stage 순서대로 실행.
- **캐싱 전략**: Stage 0 결과가 DB에 있으면 재사용(단, force_rerun=True 시 새 호출). Stage 1은 Stage 0 결과가 없으면 에러.
- **확장성**: `PIPELINE_STAGES`의 `run_fn_name`을 호출하는 구조로 Stage 추가 시 확장 용이.

## 3. Stage별 구조
- **Stage 0: Job Research**
  - 입력: company_name, job_title, manual_jd_text(optional).
  - 0.1 Collect: `llm_client.call_job_research_collect`(web_search, prompt `job_research_collect.txt`) → raw_sources 저장.
  - 0.2 Summarize: `llm_client.call_job_research_summarize`(prompt `job_research_summarize.txt`) → raw_job_desc, research_sources.
  - 출력: JobResearchCollectResult(raw_sources), JobResearchResult(raw_job_desc, research_sources) + UI용 llm_raw_text/llm_error.
  - 영속화: SQLite에 저장/조회(job_research_collect_results, job_research_results).
- **Stage 1: IVC**
  - 입력: JobInput(job_meta + raw_job_desc).
  - 1-A Task Extractor: `IVCTaskExtractor.run` → `task_atoms[]` (LLM JSON 또는 스텁).
  - 1-B Phase Classifier: `IVCPhaseClassifier.run` → `ivc_tasks[]`, `phase_summary`, `task_atoms` 첨부.
  - 오케스트레이션: `core/ivc/pipeline.py::run_ivc_pipeline` → `PipelineManager.run_stage_1_ivc`.
  - 영속화: 아직 없음(메모리/세션 보관).
- **Stage 2~3**: dna/workflow 스텁만 존재(미구현).

## 4. LLM/프롬프트/로깅
- **LLM**: Gemini web_browsing(google-genai). 기본 `gemini-2.5-flash`(env `GEMINI_MODEL`). 키/SDK 없으면 스텁. Stage 1은 `call_task_extractor` / `call_phase_classifier` 헬퍼로 동일한 파서/스텁/로그 정책을 공유한다.
- **프롬프트**: `prompts/job_research_collect.txt`, `prompts/job_research_summarize.txt`, `prompts/ivc_task_extractor.txt`, `prompts/ivc_phase_classifier.txt`. JSON-only 규칙, 코드블록 금지, one-shot 예시 포함.
- **로깅**: `infra/logging_config.setup_logging`이 콘솔/파일 핸들러 구성(중복 방지 플래그 사용). UI에서 `logs/app.log` tail을 expander로 노출.

## 5. 테스트 및 관측 포인트
- 테스트: `ax_agent_factory/tests`에서 DB 캐시, Stage 0 결과 저장, Stage 1 파이프라인 파싱/스텁 동작 검증.
- 관측: Stage별 logger 사용, UI 탭에서 LLM raw/error 확인. 향후 JSON 밸리데이션 강화/메트릭 추가 예정.
