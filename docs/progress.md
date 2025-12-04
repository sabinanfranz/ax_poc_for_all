# Progress Log
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## Stage/기능 진행 현황
| Stage | 상태 | 비고 |
| --- | --- | --- |
| 0. Job Research | ✔ 구현/DB 저장 | Gemini web_browsing 래퍼 + 스텁, UI 탭에 raw/error 표시 |
| 1. IVC (Task Extractor → Phase Classifier) | ✔ 구현(Gemini, 키 없으면 스텁) | call_task_extractor / call_phase_classifier + sanitizer + 파이프라인 연결 |
| 1.3 Static Classifier | ✔ 구현(Gemini, 키 없으면 스텁) | call_static_task_classifier + job_tasks static_* 업데이트 |
| 2. DNA | 📝 스텁 | core/dna.py NotImplemented |
| 2. Workflow(2.1 Struct → 2.2 Mermaid) | ✔ 구현(LLM/스텁) | call_workflow_struct / call_workflow_mermaid, UI 탭/테스트 포함, workflow_results에 plan/mermaid 캐시 |
| 4~9. AX/Agent/Skill/Prompt/Runner | 📝 기획 | 스펙만 유지, 코드 없음 |

## 최근 업데이트(요약)
- Stage 2 Workflow 결과(plan/mermaid) `workflow_results` 테이블 캐시 추가, UI가 세션 없을 때 DB/로그로 폴백.
- LLM override(Fake) 호출도 llm_call_logs에 기록하도록 개선.
- Phase Classifier 분류 근거 누락 시 llm_error 노출 강화 및 프롬프트 명시.

## 다음 스프린트 우선순위
- Stage 0/1/2 캐시 재사용 옵션 및 부분 재실행 정책 명확화.
- Stage 2(DNA) 스키마·프롬프트 확정 후 최초 구현.
- UI에서 job_tasks 기반 요약(Static/Workflow 메타) 노출 고도화.
- WorkflowResults 조회/관리용 보조 화면 및 Mermaid 렌더 오류 핸들링 추가 검토.
