# AX Agent Factory – Database & Table Doc
> Purpose: DB/Stage/UI 매핑 한눈에 보기  
> Last updated: 2025-12-04 by AX Database & Table Doc Architect  
> Sources: docs/schema.md, docs/prd.md, core/infra/db.py, core/pipeline_manager.py, Streamlit UI(app.py), models/job_run.py

## 1. 개요
- 엔진/경로: SQLite, 기본 `data/ax_factory.db` (`AX_DB_PATH`로 변경 가능), `infra/db.py::_ensure_tables`가 자동 생성.
- 범위: Stage 0~2.2 구현 + AX Stage 4~7 스키마/테이블 제안(미구현).
- 원칙: LLM 응답 JSON은 각 Stage top-level 키만 포함하고 `llm_raw_text/llm_cleaned_json/llm_error`는 Runner가 사후 주입.

## 2. 전체 파이프라인 & 테이블 개요
| Stage | 주요 입력 | 주요 출력(top-level) | DB 적재/조회 |
| --- | --- | --- | --- |
| 0.1 Collect | JobRun(company_name, job_title, manual_jd_text?) | job_meta, raw_sources | INSERT job_research_collect_results(raw_sources_json, job_meta_json) |
| 0.2 Summarize | job_meta + raw_sources | raw_job_desc, research_sources | INSERT/UPSERT job_research_results(raw_job_desc, research_sources_json) |
| 1.1 Task Extractor | job_meta, raw_job_desc | task_atoms | UPSERT job_tasks(task_* 기본 컬럼) |
| 1.2 Phase Classifier | job_meta, task_atoms, raw_job_desc? | ivc_tasks, phase_summary, task_atoms | UPDATE job_tasks ivc_* 컬럼 |
| 1.3 Static Classifier | PhaseClassificationResult | task_static_meta, static_summary | UPDATE job_tasks static_* 컬럼 |
| 2.1 Workflow Struct | PhaseClassificationResult(+task_static_meta optional) | stages/streams/nodes/edges/entry/exit | UPDATE job_tasks workflow_* 플래그, REPLACE job_task_edges, UPSERT workflow_results.workflow_plan_json |
| 2.2 Workflow Mermaid | WorkflowPlan | workflow_name, mermaid_code, warnings | UPSERT workflow_results.mermaid_code/warnings_json (+ plan_json 보강) |
| 4~7 AX (설계) | Workflow/Agents/Skills | AXWorkflowDesignResult 등 | 제안 테이블: ax_workflows/ax_agents/ax_agent_task_links/ax_deep_research_results/ax_skill_cards/ax_prompts |

## 3. Stage ↔ DB 테이블 매핑
- Stage 0.1 Collect  
  - 출력: job_meta, raw_sources  
  - DB: job_research_collect_results.raw_sources_json, job_meta_json; job_run_id로 UNIQUE.
- Stage 0.2 Summarize  
  - 출력: raw_job_desc, research_sources  
  - DB: job_research_results.raw_job_desc, research_sources_json; job_run_id로 UNIQUE.
- Stage 1.1 Task Extractor  
  - 출력: task_atoms[*](task_id, task_original_sentence, task_korean, task_english?, notes?)  
  - DB: job_tasks INSERT/UPSERT 기본 컬럼(task_original_sentence, task_korean, task_english, notes).
- Stage 1.2 Phase Classifier  
  - 출력: ivc_tasks[*](ivc_phase, ivc_exec_subphase?, primitive_lv1, classification_reason), phase_summary  
  - DB: job_tasks UPDATE ivc_phase/ivc_exec_subphase/primitive_lv1/classification_reason.
- Stage 1.3 Static Classifier  
  - 출력: task_static_meta[*](static_type_lv*, domain_lv*, rag_required, rag_reason, value/complexity/value_complexity_quadrant, recommended_execution_env, autoability_reason, data_entities[], tags[])  
  - DB: job_tasks UPDATE static_type_lv1/2, domain_lv1/2, rag_required(0/1), rag_reason, value_score, complexity_score, value_complexity_quadrant, recommended_execution_env, autoability_reason, data_entities_json, tags_json.
- Stage 2.1 Workflow Struct  
  - 출력: nodes(stage_id, stream_id, label, is_entry/is_exit/is_hub), edges(source,target,label?), (static_result가 있을 경우 task_static_meta/static_summary 포함)  
  - DB: job_tasks UPDATE stage_id/stream_id/workflow_node_label/is_entry/is_exit/is_hub; job_task_edges REPLACE ALL rows for job_run_id; workflow_results.workflow_plan_json UPSERT.
- Stage 2.2 Workflow Mermaid  
  - 출력: workflow_name, mermaid_code, warnings  
  - DB: workflow_results.mermaid_code, warnings_json (workflow_plan_json이 있으면 보강).
- AX Stage 4~7 (설계)  
  - AXWorkflowDesignResult → ax_workflows, (선택) ax_agents/ax_agent_task_links 시드  
  - AgentSpecsForPromptBuilder → ax_agents(upsert), agent_spec_json  
  - DeepSkillResearchResult → ax_deep_research_results  
  - SkillCardSet → ax_skill_cards (+ agent_skill_map 반영)  
  - AgentPromptSet → ax_prompts per AgentPromptBundle

## 4. 테이블별 상세 스펙
- job_runs  
  - 목적: 파이프라인 루트 식별자.  
  - 라이프사이클: INSERT create_or_get_job_run, READ 전 Stage, UPDATE status/meta.  
  - 주요 컬럼: company_name, job_title, industry_context?, business_goal?, manual_jd_text?, status?, created_at/updated_at.
- job_research_collect_results  
  - 목적: Stage 0.1 raw_sources 캐시.  
  - 라이프사이클: UPSERT save_job_research_collect_result, READ summarize or UI.  
  - 컬럼: job_meta_json?, raw_sources_json, created_at/updated_at.
- job_research_results  
  - 목적: Stage 0.2 최종 요약.  
  - 라이프사이클: UPSERT save_job_research_result, READ Stage 1 입력/UI.  
  - 컬럼: raw_job_desc, research_sources_json, created_at/updated_at.
- job_tasks  
  - 목적: 모든 태스크/분류/정적/워크플로우 메타 저장.  
  - 라이프사이클: INSERT/UPSERT save_task_atoms, UPDATE apply_ivc_classification, UPDATE apply_static_classification, UPDATE apply_workflow_plan.  
  - 컬럼: task_original_sentence, task_korean, task_english?, notes?, ivc_phase/ivc_exec_subphase/primitive_lv1/classification_reason, static_type_lv1/2, domain_lv1/2, rag_required(0/1), rag_reason, value_score, complexity_score, value_complexity_quadrant, recommended_execution_env, autoability_reason, data_entities_json, tags_json, stage_id, stream_id, workflow_node_label, is_entry/is_exit/is_hub, review_status?, created_at/updated_at.  
  - 키: UNIQUE(job_run_id, task_id).
- job_task_edges  
  - 목적: 워크플로우 엣지.  
  - 라이프사이클: DELETE+INSERT in apply_workflow_plan.  
  - 컬럼: source_task_id, target_task_id, label?, created_at/updated_at.
- workflow_results  
  - 목적: WorkflowPlan/MermaidDiagram 캐시(세션 리셋 대비).  
  - 라이프사이클: UPSERT save_workflow_plan/save_workflow_mermaid_result, READ UI 폴백.  
  - 컬럼: workflow_plan_json, mermaid_code, warnings_json, created_at/updated_at (job_run_id UNIQUE).
- llm_call_logs  
  - 목적: 모든 LLM 호출 메타/파싱 상태 기록.  
  - 라이프사이클: INSERT save_llm_call_log, READ get_llm_calls_by_job_run.  
  - 컬럼: stage_name, model_name, prompt_version?, input_payload_json, output_text_raw?, output_json_parsed?, status, error_type/message?, latency_ms?, tokens_*.
- AX 제안 테이블 (미구현)  
  - ax_workflows: AXWorkflowDesignResult 전체 저장.  
  - ax_agents: AgentSpecsForPromptBuilder.agents 등 저장.  
  - ax_agent_task_links: agent_id ↔ task_id 매핑.  
  - ax_deep_research_results: DeepSkillResearchResult 저장.  
  - ax_skill_cards: SkillCardSet 저장.  
  - ax_prompts: AgentPromptSet 저장.

## 5. UX / UI ↔ DB 매핑
- Streamlit 메인 페이지(app.py)  
  - Stage 탭: 0.1/0.2/1.1/1.2/1.3/2.1/2.2 모두 세션 우선; 세션이 비어도 0.x는 job_research_*, 1.x/2.1은 job_tasks/job_task_edges, 2.1/2.2는 workflow_results/LLM 로그에서 폴백 조회.  
  - Workflow Struct 탭: 세션 plan이 없어도 DB의 job_tasks/job_task_edges 및 workflow_results.workflow_plan_json을 병렬로 표시. Mermaid 탭도 workflow_results/LLM 로그 폴백을 사용.  
  - Mermaid 미리보기: mermaid_code 렌더링(네트워크로 CDN 로드).  
  - 로그: logs/app.log tail만 표시(LLM 로그 DB는 UI 미노출).  
  - UI에서 job_tasks/job_task_edges/llm_call_logs 직접 조회 화면은 없음(추가 화면 필요).

## 6. 일관성 체크 결과 (이슈/TO-DO)
- AX 테이블/스키마는 문서에 정의만 있고 실제 DB 생성/Runner 연계 미구현. Stage 4~7 구현 시 llm_call_logs 정책 재사용 필요.
- job_task_edges.label 컬럼을 LLM이 채우지 않아 대부분 NULL/빈 문자열 예상. 사용 계획이 있다면 프롬프트/파서에서 값 반영 필요.
- job_tasks.review_status 컬럼이 DB에 있지만 어떤 Stage에서도 설정하지 않음. HITL 플로우가 필요하면 Runner/UI 처리 추가 필요.
- job_research_collect_results.job_meta_json은 저장되지만 UI에서 직접 노출하지 않음(0.2 입력에는 사용). UI 노출 필요 시 추가 탭/섹션 검토.
