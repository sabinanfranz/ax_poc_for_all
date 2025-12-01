# Usage Guide (AX Agent Factory v1.1)

## 빠른 실행 (PowerShell 예시)
```powershell
$Env:GOOGLE_API_KEY="your-valid-key"; $Env:GEMINI_MODEL="gemini-2.5-flash"; $Env:AX_DB_PATH="C:\Users\admin\Desktop\ax_poc\data\ax_factory.db"; streamlit run ax_agent_factory/app.py
```
- `GOOGLE_API_KEY` 없으면 스텁 응답.
- `GEMINI_MODEL` 생략 시 기본 `gemini-2.5-flash`.
- `AX_DB_PATH` 생략 시 기본 `data/ax_factory.db`.

## .env 로드 (PowerShell)
```powershell
Get-Content .env | % { if ($_ -match '^(?<k>[^=]+)=(?<v>.*)$') { Set-Item Env:$($matches['k']) $matches['v'] } }
```

## UI 사용
1) 사이드바에 회사명/직무명 입력, 필요시 JD 텍스트 입력.  
2) `0. Job Research 실행` 또는 `0~1단계 실행` 버튼 클릭.  
3) Stage 탭:
   - Stage 0: 결과/LLM 응답-에러 탭 확인.
   - Stage 1: task_atoms (Extractor), ivc_tasks/phase_summary (Classifier), 설명 탭에서 IO/경로 확인.

## 테스트
```powershell
python -m pytest ax_agent_factory/tests
```

## 주요 경로
- UI: `ax_agent_factory/app.py`
- 오케스트레이션: `core/pipeline_manager.py`
- Stage 0: `core/research.py` + `infra/llm_client.py` + `infra/db.py`
- Stage 1: `core/ivc/{task_extractor, phase_classifier, pipeline}.py`
- 프롬프트: `ax_agent_factory/prompts/*.txt` (로더: `infra/prompts.py`)
- 기본 DB: `data/ax_factory.db` (환경변수 `AX_DB_PATH`로 변경 가능)
