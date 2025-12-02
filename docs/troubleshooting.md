# Troubleshooting
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## LLM/JSON 관련
- **API 키 없음/오류**: `GOOGLE_API_KEY`가 없거나 잘못되면 Stage 0/1이 스텁으로 동작한다. 실제 호출이 필요하면 유효한 키와 web_browsing 지원 모델(`gemini-2.5-flash` 등) 설정.
- **JSON 파싱 실패**: `_extract_json_from_text`가 코드블록/잡설을 제거해도 `{}`가 없으면 InvalidLLMJsonError가 발생. Stage 0은 `_stub_job_research`로, Stage 1은 `_stub_result`로 폴백. UI의 “LLM 응답/에러” 탭에서 raw/error 확인.
- **모델 기능 미지원**: web_search 미지원 모델로 호출 시 응답이 비어 파싱 실패 가능 → `GEMINI_MODEL`을 기본값으로 되돌린다.

## 환경 변수/경로
- **ModuleNotFoundError**: 항상 리포 루트에서 `streamlit run ax_agent_factory/app.py` 실행. `ax_agent_factory/__init__.py` 존재 여부 확인.
- **DB 경로/권한 문제**: 기본 `data/ax_factory.db`, 환경변수 `AX_DB_PATH`로 변경 가능. 경로가 없는 경우 자동 생성되지만, 쓰기 권한이 없으면 실패 → 다른 경로로 지정.
- **.env 로드**(PowerShell):  
  `Get-Content .env | % { if ($_ -match '^(?<k>[^=]+)=(?<v>.*)$') { Set-Item Env:$($matches['k']) $matches['v'] } }`

## UI/파이프라인 증상별
- **버튼 반응 없음**: 회사명/직무명 필수. Stage 1은 Stage 0 결과가 DB/세션에 있어야 한다.
- **task_atoms가 비어 있음**: LLM 스텁이 동작했거나 Stage 1 미실행. Stage 1 실행 시 파이프라인이 `task_atoms`를 Phase 결과에 다시 붙여서 UI에 노출한다.
- **로그 중복/시끄러움**: `infra/logging_config.setup_logging`은 중복 호출을 방지하는 플래그를 가진다. Streamlit 재실행으로 로그 핸들러가 2중 등록되면 세션 재시작.

## 테스트/검증
- 실행: `python -m pytest ax_agent_factory/tests`
- ImportError 발생 시 루트에서 실행하거나 `PYTHONPATH`에 리포 루트를 추가.

## 프롬프트/설정 변경 후 갱신
- `ax_agent_factory/prompts/*.txt` 수정 후 Streamlit 세션을 재시작하거나 `infra.prompts.load_prompt.cache_clear()`로 캐시를 지운다.
- 모델 변경은 `GEMINI_MODEL`로, DB 위치 변경은 `AX_DB_PATH`로 제어한다.
