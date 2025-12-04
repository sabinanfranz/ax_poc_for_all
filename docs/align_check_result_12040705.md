# Schema–Prompt Align 체크 결과 (prompts = source of truth)
> Last updated: 2025-12-04 07:05

- 기준: 프롬프트를 정본으로 보고, Pydantic 스키마/파이프라인/DB가 따라야 함.
- 비교 대상: `ax_agent_factory/prompts/*.txt` vs `core/schemas/*.py` vs 파이프라인 코드. 샘플 출력 없음.

## Status 스냅샷
| stage_id | prompt_file | result_type_name | status | 주요 이슈(스키마/코드 측) |
| --- | --- | --- | --- | --- |
| stage0_1_job_collect | job_research_collect.txt | JobResearchCollectResult | WARN | 프롬프트는 `job_meta + raw_sources` 출력, 스키마/DB는 `raw_sources`만 |
| stage0_2_job_summarize | job_research_summarize.txt | JobResearchResult | OK | 정합 |
| stage1_1_task_extractor | ivc_task_extractor.txt | TaskExtractionResult | WARN | industry_context 프롬프트 optional, 스키마 필수 |
| stage1_2_phase_classifier | ivc_phase_classifier.txt | PhaseClassificationResult | WARN | industry_context 프롬프트 optional, 스키마 필수 |
| stage1_3_static_classifier | static_task_classifier.txt | StaticClassificationResult | OK | 프롬프트 enum이 스키마 자유 문자열보다 좁아 무해 |
| stage2_1_workflow_struct | workflow_struct.txt | WorkflowPlan | WARN | 프롬프트 입력에 task_static_meta 요구, 파이프라인에서 미전달 |
| stage2_2_workflow_mermaid | workflow_mermaid.txt | MermaidDiagram | OK | 정합 |

## Stage별 노트
- **stage0_1_job_collect (WARN)**  
  - Gap: 스키마/DB가 job_meta를 누락하고 industry_context 네이밍 불일치.  
  - 권장: JobResearchCollectResult 스키마와 DB를 job_meta 포함, industry_context 필드로 정규화.
- **stage1_1_task_extractor (WARN)**  
  - Gap: JobMeta.industry_context를 프롬프트는 optional, 스키마는 필수.  
  - 권장: 스키마를 optional로 완화하거나 호출 전 default 주입.
- **stage1_2_phase_classifier (WARN)**  
  - Gap 동일: industry_context optional vs 스키마 필수.  
  - 권장: 위와 동일 조정. 나머지 enum/phase_summary/필드 구조는 이미 합치.
- **stage2_1_workflow_struct (WARN)**  
  - Gap: 프롬프트는 task_static_meta 입력을 요구하나 `core/workflow.py` payload는 전달하지 않음.  
  - 권장: payload에 task_static_meta 추가 또는 프롬프트를 optional로 명시.

## 우선 수정안
1) JobMeta.industry_context를 optional로 완화하거나 기본값 주입 경로 추가(스키마/파이프라인).  
2) JobResearchCollectResult 스키마/DB에 job_meta 포함 + industry_context 네이밍 통일.  
3) Workflow Struct 호출 시 task_static_meta를 전달(또는 프롬프트에 optional 표시).  

