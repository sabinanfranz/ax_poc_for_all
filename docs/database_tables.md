# Database & Tables
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 1) Connection & Path
- SQLite (default): `data/ax_factory.db` (`AX_DB_PATH`로 변경 가능)
- 초기화: `infra/db.py::_ensure_tables`가 Streamlit/테스트 구동 시 자동 실행
- 로그: LLM 호출은 `llm_call_logs`에 stage_name/status/token 메타를 기록

## 2) Core Tables (Stage 0~2)
- **job_runs**  
  id PK, company_name, job_title, industry_context?, business_goal?, manual_jd_text?, status?, created_at/updated_at
- **job_research_collect_results** (0.1)  
  job_run_id UNIQUE FK, raw_sources_json, job_meta_json?, created_at/updated_at
- **job_research_results** (0.2)  
  job_run_id UNIQUE FK, raw_job_desc, research_sources_json, created_at/updated_at
- **job_tasks** (Stage 1/1.3/2.1)  
  job_run_id FK, task_id UNIQUE per job_run, task_original_sentence/task_korean/task_english/notes, ivc_* (phase/subphase/primitive/reason), static_* (type/domain/rag/value/complexity/env/tags/entities), workflow_* (stage_id/stream_id/label/is_entry/is_exit/is_hub), review_status, created_at/updated_at
- **job_task_edges** (2.1)  
  job_run_id FK, source_task_id, target_task_id, label?, created_at/updated_at
- **llm_call_logs**  
  stage_name, model_name, prompt_version?, input_payload_json, output_text_raw?, output_json_parsed?, status(success|json_parse_error|api_error|stub_fallback), error_type/message?, latency_ms?, tokens_*?, created_at

## 3) AX Tables (Stage 4~7, 제안)
- **ax_workflows**  
  job_run_id FK, workflow_name/summary, ax_workflow_mermaid_code, agent_table_json, n8n_workflows_json, sheet_schemas_json, validator_plan_json, observability_plan_json, created_at/updated_at
- **ax_agents**  
  job_run_id FK, agent_id (job_run 내 UNIQUE), agent_name, stage_stream_step, agent_type, execution_environment, n8n_workflow_id/node_name, primary_sheet?, rag_enabled?, file_search_corpus_hint?, domain_context, role_and_goal, success_metrics_json?, error_policy?, validation_policy?, notes?, agent_spec_json, created_at/updated_at
- **ax_agent_task_links**  
  job_run_id FK, agent_id, task_id, link_type(primary/secondary/validator/observer 등), notes?, created_at/updated_at
- **ax_deep_research_results**  
  job_run_id FK, agent_id, research_focus, research_sections_json, created_at/updated_at
- **ax_skill_cards**  
  job_run_id FK, skill_public_id (job_run 내 UNIQUE), skill_name, target_agent_ids_json, related_task_ids_json, purpose, when_to_use, core_heuristics_json, step_checklist_json, bad_signs_json, good_signs_json, created_at/updated_at
- **ax_prompts**  
  job_run_id FK, agent_id, execution_environment, prompt_version, single_prompt?, system_prompt?, user_prompt_template?, logic_hint?, human_checklist?, examples_json?, mode?, created_at/updated_at

## 4) LLM JSON 규칙 (요약)
- LLM 응답은 **단일 JSON 객체**만, 허용된 top-level 키만 사용
- Stage별 top-level 키  
  - 0.1 Collect: ["job_meta","raw_sources"]  
  - 0.2 Summarize: ["raw_job_desc","research_sources"]  
  - 1.1 Task Extractor: ["job_meta","task_atoms"]  
  - 1.2 Phase Classifier: ["job_meta","raw_job_desc","task_atoms","ivc_tasks","phase_summary"]  
  - 1.3 Static Classifier: ["job_meta","task_static_meta","static_summary"]  
  - 2.1 Workflow Struct: ["workflow_name","workflow_summary","stages","streams","nodes","edges","entry_points","exit_points","notes"]  
  - 2.2 Workflow Mermaid: ["workflow_name","mermaid_code","warnings"]  
  - 4. AX Workflow Architect: ["workflow_name","workflow_summary","ax_workflow_mermaid_code","agent_table_for_agent_architect","n8n_workflows","sheet_schemas","validator_plan","observability_plan"]  
  - 5. Agent Architect: ["stage_context","global_policies","agents"]  
  - 6-A Deep Skill Research: ["agent_id","research_focus","research_sections"]  
  - 6-B Skill Extractor: ["skill_cards","agent_skill_map"]  
  - 7. Prompt Builder: ["summary","agents"]
- `llm_raw_text / llm_cleaned_json / llm_error`는 LLM 응답에 포함하지 않고 Runner가 결과 객체에 사후 주입한다.

## 5) 운영 메모
- DB는 빈 상태에서도 `_ensure_tables`가 컬럼을 추가하며, legacy 컬럼(raw_sources/research_sources 등)은 COALESCE로 호환.
- AX 테이블은 설계안이며, 구현 시 `_add_column_if_missing` 사용해 마이그레이션 내결함성을 유지.
- 스텁/LLM 실패 시에도 파이프라인은 진행하도록 status=stub_fallback/json_parse_error를 로그에 남긴다.
