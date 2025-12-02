# Usage Guide
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## 1) 환경 준비
- Python 3.10+ 권장, 가상환경 사용.
- 의존성 설치:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
- 필수/선택 환경변수  
  - `GOOGLE_API_KEY`: 없으면 Stage 0이 스텁으로 동작(데모용).  
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
  - `0. Job Research 실행`: Stage 0만 실행, 결과를 DB/세션에 저장.
  - `0~1단계 실행 (Job Research → IVC)`: Stage 0 실행 후 바로 Stage 1(IVC)까지 수행.
- 로그: `logs/app.log`가 자동 생성되며, UI 하단 expander에서 tail 확인 가능.

## 3) 결과 확인 (탭 안내)
- **Stage 0 탭**
  - Job Research 결과: `raw_job_desc`, `research_sources` 확인.
  - LLM 응답/에러: `_raw_text`/`llm_error` 확인(파싱 실패 시 스텁/에러 노출).
- **Stage 1 탭**
  - 실행/결과: Task Extractor의 `task_atoms[]`, Phase Classifier의 `ivc_tasks[]`, `phase_summary`.
  - 설명/IO: 입력/프롬프트/오케스트레이션 경로 안내.
- LLM 키가 없거나 `LLMClient.call` 미구현 상태에서는 Stage 1이 스텁 결과를 보여준다(동작 검증용).

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
