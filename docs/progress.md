# Progress Log
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## Stage/기능 진행 현황
| Stage | 상태 | 비고 |
| --- | --- | --- |
| 0. Job Research | ✔ 구현/DB 저장 | Gemini web_browsing 래퍼 + 스텁, UI 탭에 raw/error 표시 |
| 1. IVC (Task Extractor → Phase Classifier) | ✔ 구현(Gemini, 키 없으면 스텁) | call_task_extractor / call_phase_classifier + sanitizer + 파이프라인 연결 |
| 1.3 Static Classifier | ✔ 구현(Gemini, 키 없으면 스텁) | call_static_task_classifier + job_tasks static_* 업데이트 |
| 2. DNA | 📝 스텁 | core/dna.py NotImplemented |
| 2. Workflow(2.1 Struct → 2.2 Mermaid) | ✔ 구현(LLM/스텁) | call_workflow_struct / call_workflow_mermaid, UI 탭/테스트 포함 |
| 4~9. AX/Agent/Skill/Prompt/Runner | 📝 기획 | 스펙만 유지, 코드 없음 |

## 최근 업데이트(요약)
- Stage 0 legacy 컬럼 호환 저장 및 NOT NULL 이슈 해결.
- Stage 1.3 Static classifier 추가, job_tasks static_* 영속화.
- Stage 메타/ui_label/ui_group/ui_step 추가, “다음 단계 실행” 순차 런너/버튼 도입.
- 모든 Stage 프롬프트/LLM 호출 기본 max_tokens 81920으로 상향.
- UI: 0.1~2.2 탭 공통 서브탭(Input/결과/LLM Raw/Clean/Error/설명/I/O) 유지, “다음 단계 실행”으로 0.2→1.2→1.3→2.2 자연 이동.

## 다음 스프린트 우선순위
- Stage 0/1/2 캐시 재사용 옵션 및 부분 재실행 정책 명확화.
- Stage 2(DNA) 스키마·프롬프트 확정 후 최초 구현.
- UI에서 job_tasks 기반 요약(Static/Workflow 메타) 노출 고도화.
