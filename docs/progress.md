# Progress Log – AX Agent Factory (v1.1 PoC 기준)

## 오늘 수행한 주요 작업
- 레포 정리: 실제 실행 기준을 `ax_agent_factory/` 패키지로 일원화, 구 스캐폴드(`app/`, `core/`, `infra/`, 루트 `prompts/`, 루트 `tests/`) 제거.
- Stage 0/1 파이프라인 확립:
  - Stage 0 Job Research: PipelineManager → llm_client(Gemini web_search) → DB 저장 → UI 탭.
  - Stage 1 IVC: Task Extractor/Phase Classifier 파이프라인 연결, 결과(UI) 분리 표시, task_atoms 전달.
- 프롬프트 외부화: `ax_agent_factory/prompts/*.txt`로 분리, 로더(`infra/prompts.py`) 통해 주입.
- LLM 에러 처리 개선: `_clean_json_text`로 코드펜스 제거, 파싱 실패 시 스텁으로 폴백하되 LLM 원문/에러를 UI에 노출.
- UI 개선:
  - Stage 0/1 탭을 실행/결과 vs 설명/IO로 분리.
  - LLM raw/에러 표시를 위한 서브탭 추가.
  - Stage 1에서 task_atoms와 ivc_tasks를 분리 표시(파이프라인에서 task_atoms 전달).
- 모델 기본값: `gemini-2.5-flash`로 업데이트, `GEMINI_MODEL` 환경변수로 override 가능.
- 문서 업데이트:
  - `docs/prd.md`를 v1.1 상태로 갱신, `docs/prd_v1.1.md` 신규 생성.
  - `docs/architecture.md`, `docs/prompt_guidelines.md`에 외부 프롬프트/LLM 전략/모듈 구조 반영.
- 테스트 보강:
  - Job Research 디버그 정보 전달 테스트 추가.
  - 파싱 실패 시 스텁 반환 및 UI 표시를 검증하기 위한 기반 마련.

## 현재 시스템 동작 흐름 (요약)
- Streamlit UI → PipelineManager
- Stage 0: `call_gemini_job_research`(web_search) → `_clean_json_text` → JSON 파싱 실패 시 스텁 + raw/에러 첨부 → DB 저장 → UI 탭에서 raw_job_desc, sources, raw/err 표시
- Stage 1: Task Extractor(프롬프트: `prompts/ivc_task_extractor.txt`) → Phase Classifier(`prompts/ivc_phase_classifier.txt`) → ivc_tasks/phase_summary + task_atoms 전달 → UI 탭 분리 표시
- DB: 기본 `data/ax_factory.db` (환경변수 `AX_DB_PATH`로 변경 가능)
- 모델: 기본 `gemini-2.5-flash` (`GEMINI_MODEL`로 override)

## 실행/테스트 요약
- 환경 설정(예, PowerShell 한 줄):
  ```
  $Env:GOOGLE_API_KEY="your-valid-key"; $Env:GEMINI_MODEL="gemini-2.5-flash"; $Env:AX_DB_PATH="C:\Users\admin\Desktop\ax_poc\data\ax_factory.db"; streamlit run ax_agent_factory/app.py
  ```
- 테스트: `python -m pytest ax_agent_factory/tests`

## 개선 과정에서 배운 포인트
- LLM 응답에 ```json 코드펜스나 여분 문자열이 섞이면 파싱이 실패하므로, `_clean_json_text`로 펜스 제거 후 첫 `{`~마지막 `}` 슬라이스가 필요함.
- 파싱 실패 시 예외를 던지기보다 스텁 + raw/에러를 함께 반환하면 UI/디버깅 흐름이 끊기지 않음.
- 프롬프트를 파일로 외부화하면 (1) 수정 시 코드 변경 불필요, (2) 테스트에서 로더를 쉽게 모킹 가능.
- Stage별 탭을 실행/설명으로 분리하면 사용자와 개발자가 각각 필요한 정보를 빠르게 확인할 수 있음.
- 패키지 경로 문제는 `sys.path` 보정이나 명시적 패키지 구조 정리(`__init__.py`)로 해결해야 스트림릿 실행 시 ModuleNotFound 에러를 방지할 수 있음.
- 기본 모델/경로를 환경변수로 통일해두면 (GEMINI_MODEL, AX_DB_PATH) 운영/테스트 환경 전환이 쉬움.
