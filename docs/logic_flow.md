# Logic Flow (Current v1.1 PoC)

## 공통 전제
- 실행 경로: `ax_agent_factory/`
- 환경변수:
  - `GOOGLE_API_KEY` (필수, 없으면 스텁)
  - `GEMINI_MODEL` (기본 `gemini-2.5-flash`, web_search 지원)
  - `AX_DB_PATH` (기본 `data/ax_factory.db`)
- DB: SQLite, 테이블 `job_runs`, `job_research_results`
- 프롬프트: `ax_agent_factory/prompts/*.txt` (loader: `infra/prompts.py`)

## Stage 0 – Job Research
1. UI 입력 (Streamlit)
   - 파일: `app.py`
   - 사이드바: `company_name`, `job_title`, `manual_jd_text`, 버튼(`0단계`, `0~1단계`)
2. 파이프라인 호출
   - 클래스: `core/pipeline_manager.py::PipelineManager`
   - 메서드: `run_stage_0_job_research(job_run, manual_jd_text, force_rerun)`
   - 캐시: DB에 결과 있으면 반환(단, force_rerun=True 시 재실행)
3. JobRun 생성
   - `infra/db.py::create_job_run` (id, company_name, job_title, created_at 저장)
4. LLM 호출
   - 함수: `infra/llm_client.py::call_gemini_job_research`
   - 프롬프트: `prompts/job_research.txt` (치환: company_name, job_title, manual_jd_text)
   - 모델: `GEMINI_MODEL` 또는 기본 `gemini-2.5-flash`
   - 도구: `google_search` Tool with `types.Tool(google_search=types.GoogleSearch())`
5. 응답 파싱
   - 정제: `_clean_json_text` (코드펜스 제거, 첫 `{`~마지막 `}` 슬라이스)
   - 파싱 실패: `_stub_job_research`로 폴백 + `llm_error`, `raw_text` 포함
   - 정상 파싱: `_raw_text`를 결과 dict에 포함
6. 결과 매핑/저장
   - 모델: `models/job_run.py::JobResearchResult`
   - 보조 필드: `llm_raw_text`, `llm_error` 동적 속성 부여
   - DB 저장: `infra/db.py::save_job_research_result`
7. UI 표시
   - 탭: Stage 0 → 내부 탭 2개
     - "Job Research 결과": `raw_job_desc`, `research_sources`
     - "LLM 응답/에러": `llm_raw_text`, `llm_error` (없으면 안내)
   - 설명 탭: 입력/LLM/저장/파일 경로 안내

## Stage 1 – IVC (Task Extractor → Phase Classifier)
전제 입력: Stage 0 `raw_job_desc` + `job_meta`

1. UI 실행
   - 버튼 `0~1단계 실행` → Stage 0 후 Stage 1 연속 실행
2. 파이프라인 호출
   - `core/pipeline_manager.py::run_stage_1_ivc(job_run, job_research_result, llm_client)`
   - Stage 0 결과가 DB에 없으면 오류
3. Task Extractor
   - 파일: `core/ivc/task_extractor.py`
   - 프롬프트: `prompts/ivc_task_extractor.txt` (`input_json` 치환)
   - LLM 호출: `LLMClient.call` (미구현 시 NotImplementedError → `_stub_result`)
   - 파싱: JSON loads → `TaskExtractionResult`
   - 스텁: raw_job_desc 기반 단일 task_atoms 생성
4. Phase Classifier
   - 파일: `core/ivc/phase_classifier.py`
   - 프롬프트: `prompts/ivc_phase_classifier.txt` (`input_json` 치환)
   - LLM 호출: `LLMClient.call` (미구현 시 `_stub_result`, 모든 태스크 SENSE)
   - 파싱: JSON loads → `PhaseClassificationResult`
   - 추가: `task_atoms`를 결과에 첨부 (파이프라인에서 전달)
5. 결과 반환
   - 함수: `core/ivc/pipeline.py::run_ivc_pipeline`
   - 출력: `PhaseClassificationResult`(ivc_tasks, phase_summary, task_atoms)
6. UI 표시
   - Stage 1 탭 → 내부 탭 2개
     - "실행/결과": task_atoms(Extractor 결과), ivc_tasks/phase_summary(Classifier 결과)
     - "설명/IO": 입력/프롬프트/출력/오케스트레이션 경로 안내

## 기타
- 기본 모델/경로 override: `GEMINI_MODEL`, `AX_DB_PATH`
- LLM 키가 없거나 SDK 미설치 시: Stage 0 스텁, Stage 1 스텁(IVC)
- 테스트:
  - `tests/test_research_stage.py`: DB 저장/ID 필요성/LLM 디버그 전달 검증
  - `tests/test_ivc_pipeline.py`: 파이프라인 happy-path/JSON 파싱 실패 검증
  - `tests/test_pipeline_manager.py`: 캐시 동작, Stage 1 실행 오류/정상 흐름 검증
