# Schema–Prompt Align 체크 결과 (prompts = source of truth)
> Last updated: 2025-12-04 07:05

- 기준: 프롬프트를 정본으로 보고, Pydantic 스키마/파이프라인/DB가 따라야 함.
- 비교 대상: `ax_agent_factory/prompts/*.txt` vs `core/schemas/*.py` vs 파이프라인 코드. 샘플 출력 없음.

## Status 스냅샷 (재검수: 현재 코드 기준)
| stage_id | prompt_file | result_type_name | status | 주요 메모 |
| --- | --- | --- | --- | --- |
| stage0_1_job_collect | job_research_collect.txt | JobResearchCollectResult | OK | 스키마/DB 모두 `job_meta` 포함, prompt와 정합 |
| stage0_2_job_summarize | job_research_summarize.txt | JobResearchResult | OK | 정합 |
| stage1_1_task_extractor | ivc_task_extractor.txt | TaskExtractionResult | OK | JobMeta.industry_context optional로 스키마/프롬프트 일치 |
| stage1_2_phase_classifier | ivc_phase_classifier.txt | PhaseClassificationResult | OK | JobMeta optional 일치, phase/summary 구조 정합 |
| stage1_3_static_classifier | static_task_classifier.txt | StaticClassificationResult | OK | prompt enum ⊂ 스키마 자유 문자열, 무해 |
| stage2_1_workflow_struct | workflow_struct.txt | WorkflowPlan | OK | pipeline이 static_result 있을 때 task_static_meta/static_summary 전달 |
| stage2_2_workflow_mermaid | workflow_mermaid.txt | MermaidDiagram | OK | 정합 |

## Stage별 노트
- **stage0_1_job_collect**: job_meta가 스키마/DB 모두 반영되어 정합.
- **stage1_1/1_2**: industry_context optional 정책이 스키마/프롬프트/코드에 일치.
- **stage2_1_workflow_struct**: static_result가 있으면 task_static_meta/static_summary를 payload에 포함하는 코드 반영 완료.

## 현재 조치 사항
- 추가 수정 필요 없음. 새 프롬프트/스키마 변경 시 Align Checker를 재실행하고 이 파일을 갱신할 것.
