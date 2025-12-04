# Usage Guide
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 1) 환경 준비
- Python 3.10+ 권장, 가상환경 사용.
- 의존성 설치:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
- 필수/선택 환경변수  
  - `GOOGLE_API_KEY`: 없으면 Stage 0/1이 스텁으로 동작(데모용).  
  - `GEMINI_MODEL`: 기본 `gemini-2.5-flash` (web_browsing 지원).  
  - `AX_DB_PATH`: 기본 `data/ax_factory.db` (경로 없으면 자동 생성).  
- .env 로드 예시(PowerShell):
```powershell
Get-Content .env | % { if ($_ -match '^(?<k>[^=]+)=(?<v>.*)$') { Set-Item Env:$($matches['k']) $matches['v'] } }
```

## 2) 실행 방법
```bash
streamlit run ax_agent_factory/app.py
```
- 브라우저가 열리면 사이드바에 회사명/직무명 입력, 필요하면 JD 텍스트를 붙여넣는다.
- 버튼
  - `▶ 다음 단계 실행`: 0.2 → 1.2 → 1.3 → 2.2 순으로 단계별 실행.
  - `0. Job Research만 실행`: 0.1/0.2까지만 실행.
  - `1. IVC까지 실행`: 0.x → 1.1/1.2까지 실행.
  - `1.3 Static까지 실행`: 0.x → 1.1/1.2/1.3까지 실행.
  - `2. Workflow까지 실행`: 전체(0~2.2) 실행.
- 로그: `logs/app.log`가 자동 생성되며, UI 하단 expander에서 tail 확인 가능.

## 3) 결과 확인 (탭 안내)
- **Stage 0 탭** (0.1 Collect / 0.2 Summarize)
  - 0.1: `raw_sources` + LLM raw/cleaned/error
  - 0.2: `raw_job_desc`, `research_sources` + LLM raw/cleaned/error
- **Stage 1 탭**
  - 1.1 Task Extractor: `task_atoms[]` + LLM raw/cleaned/error
  - 1.2 Phase Classifier: `ivc_tasks[]`, `phase_summary`, `task_atoms` + LLM raw/cleaned/error
  - 1.3 Static Classifier: `task_static_meta`, `static_summary` + LLM raw/cleaned/error
- **Stage 2 탭**
  - 2.1 Workflow Struct: `workflow_name`, `stages`, `streams`, `nodes`, `edges`, entry/exit/hub + LLM raw/cleaned/error
  - 2.2 Workflow Mermaid: `mermaid_code`(노션 호환), `warnings` + LLM raw/cleaned/error
- LLM 키/SDK가 없으면 Stage 0/1 모두 스텁으로 동작하며, `llm_error`에 사유가 남습니다.

## 4) 테스트 실행
```bash
python -m pytest ax_agent_factory/tests
```
- tmp_path로 DB를 격리하고 LLM 호출을 모킹하여 캐시/파싱/스텁 동작을 검증한다.

## 5) 참고 경로
- UI: `ax_agent_factory/app.py`
- 오케스트레이션: `core/pipeline_manager.py`
- Stage 0: `core/research.py` + `infra/llm_client.py` + `infra/db.py`
- Stage 1: `core/ivc/{task_extractor.py, phase_classifier.py, pipeline.py}`
- 프롬프트: `ax_agent_factory/prompts/*.txt` (로더: `infra/prompts.py`)
- DB 기본 경로: `data/ax_factory.db` (`AX_DB_PATH`로 변경 가능)
