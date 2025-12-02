# Progress Log
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## Stage/기능 진행 현황
| Stage | 상태 | 비고 |
| --- | --- | --- |
| 0. Job Research | ✔ 구현/DB 저장 | Gemini web_browsing 래퍼 + 스텁, UI 탭에 raw/error 표시 |
| 1. IVC (Task Extractor → Phase Classifier) | ✔ 구현(LLM 미연동 시 스텁) | 프롬프트 one-shot, JSON 스키마 명시, 파이프라인으로 연결 |
| 2. DNA | 📝 스텁 | core/dna.py NotImplemented |
| 3. Workflow | 📝 스텁 | core/workflow.py NotImplemented |
| 4~9. AX/Agent/Skill/Prompt/Runner | 📝 기획 | 스펙만 유지, 코드 없음 |

## 최근 업데이트(요약)
- Stage 0을 0.1(수집) / 0.2(정리)로 분리: collector/synthesizer 모듈과 DB 테이블 추가, 새 프롬프트 2종으로 재구성, UI에서 raw_sources 및 LLM 디버그 노출.
- 문서: PRD/Architecture/Logic Flow/Schema/Usage/Troubleshooting 정비, “Last updated” 라벨 추가.
- 코드 기준 반영: Stage 0~1 입력/출력/스키마/캐싱/스텁 전략을 문서와 일치시킴.
- UI/로깅: logs/app.log tail을 UI expander에서 노출, Stage별 탭 설명/실행 분리 유지.

## 다음 스프린트 우선순위
- LLMClient.call 실제 구현 및 모델 선택 옵션화.
- Stage 1 결과(task_atoms/ivc_tasks) 영속화 및 재사용 캐시.
- Stage 2(DNA) 스키마·프롬프트 확정 후 최초 구현.
- JSON 밸리데이션/리트라이/에러 메시지 표준화.
