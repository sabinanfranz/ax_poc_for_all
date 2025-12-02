# Progress Log
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## Stage/기능 진행 현황
| Stage | 상태 | 비고 |
| --- | --- | --- |
| 0. Job Research | ✔ 구현/DB 저장 | Gemini web_browsing 래퍼 + 스텁, UI 탭에 raw/error 표시 |
| 1. IVC (Task Extractor → Phase Classifier) | ✔ 구현(Gemini, 키 없으면 스텁) | call_task_extractor / call_phase_classifier + sanitizer + 파이프라인 연결 |
| 2. DNA | 📝 스텁 | core/dna.py NotImplemented |
| 3. Workflow | 📝 스텁 | core/workflow.py NotImplemented |
| 4~9. AX/Agent/Skill/Prompt/Runner | 📝 기획 | 스펙만 유지, 코드 없음 |

## 최근 업데이트(요약)
- Stage 0을 0.1/0.2로 분리, DB 테이블/프롬프트/UI 반영.
- Stage 1 LLM 경로를 Gemini 헬퍼(call_task_extractor/phase_classifier)로 통일, sanitizer/스텁/디버그 필드 추가.
- 파서/패턴 문서 추가: `docs/parsing_guide.md`, `docs/stage_runner.md`.
- UI: 모든 탭에 Input/결과/LLM raw/cleaned/error를 노출.

## 다음 스프린트 우선순위
- Stage 1 결과(task_atoms/ivc_tasks) 영속화 및 재사용 캐시.
- Stage 2(DNA) 스키마·프롬프트 확정 후 최초 구현.
- JSON 검증/리트라이/에러 메시지 공통화(파서 유틸 고도화).
