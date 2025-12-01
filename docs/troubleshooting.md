# Troubleshooting (AX Agent Factory v1.1)

## LLM 관련
- API 키 오류 / 400/404: `GOOGLE_API_KEY`가 유효한지 확인. 모델은 기본 `gemini-2.5-flash`, 필요 시 `GEMINI_MODEL` 설정. 키 없으면 스텁으로 동작.
- 파싱 실패: UI Stage 0 탭의 “LLM 응답/에러”에서 raw 텍스트/에러 확인. `_clean_json_text`가 코드펜스 제거 후 JSON 파싱을 시도하며, 실패 시 스텁 반환.
- web_search 미지원 모델 오류: `GEMINI_MODEL`을 web_search 지원 모델(`gemini-2.5-flash` 등)로 설정.

## 환경 변수/경로
- 모듈 경로 오류(ModuleNotFound): `ax_agent_factory/__init__.py` 존재 확인. Streamlit 실행 시 루트에서 `streamlit run ax_agent_factory/app.py` 실행.
- DB 경로 혼동: 기본 `data/ax_factory.db`. 필요 시 `AX_DB_PATH`로 명시. 패키지 내부 `ax_agent_factory/data`는 사용하지 않음.
- .env 로드(PowerShell):  
  `Get-Content .env | % { if ($_ -match '^(?<k>[^=]+)=(?<v>.*)$') { Set-Item Env:$($matches['k']) $matches['v'] } }`

## UI/파이프라인
- Stage 0/1 버튼 동작 안 함: 회사명/직무명 필수. Stage 1은 Stage 0 결과 필요.
- task_atoms 미표시: LLM 스텁 또는 파이프라인 미실행. Stage 1 실행 시 pipeline에서 task_atoms를 Phase 결과에 첨부해 UI에 표시.
- LLM 에러로 중단: 현재는 파싱 실패 시 스텁으로 반환하며, raw/에러를 UI에 표시. 실제 실패 원인은 LLM 탭에서 확인.

## 테스트
- 실행: `python -m pytest ax_agent_factory/tests`
- ImportError: 루트에서 실행하거나 `PYTHONPATH`에 루트 경로 추가.

## 기타
- 프롬프트 수정: `ax_agent_factory/prompts/*.txt` 편집 후 재실행. 로더(`infra/prompts.py`)가 캐시하므로 세션 재시작 또는 `load_prompt.cache_clear()` 필요 시 수행.
- 모델 변경: `GEMINI_MODEL` 환경변수 설정(예: `gemini-2.5-pro`).
