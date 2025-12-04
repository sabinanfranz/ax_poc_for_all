# AX Agent Factory – PRD v2 (for Codex)
> Prompt-aligned schema & implementation checklist for AX (Stage 4–7)

## 0) 목표
- 기존 Stage 0–2.2(Job Research → IVC/Static → Workflow) 위에 AX 레이어(Stage 4–7)를 추가해 하나의 파이프라인으로 완결.
- 모든 LLM 응답은 단일 JSON 객체, 허용된 top-level 키만 사용, `llm_raw_text/llm_cleaned_json/llm_error`는 LLM 응답에 포함하지 않고 Runner가 사후 주입.

## 1) 해야 할 일 (개요)
1. Pydantic 스키마 추가(`core/schemas/ax.py` 권장)
2. DB 테이블 추가(`infra/db.py` + 마이그레이션)
3. 프롬프트 파일 추가(`prompts/ax_*.txt`)
4. Stage Runner 확장(새 Stage 등록 + I/O 배선 + LLM 로그)
5. (선택) 간단한 E2E/스텁 테스트 추가

## 2) Step 1 – Pydantic 스키마 (`core/schemas/ax.py`)
- **AXWorkflowDesignResult** (Stage 4)  
  top-level: `["workflow_name","workflow_summary","ax_workflow_mermaid_code","agent_table_for_agent_architect","n8n_workflows","sheet_schemas","validator_plan","observability_plan"]`  
  필드: workflow_name, workflow_summary?, ax_workflow_mermaid_code, agent_table_for_agent_architect, n8n_workflows[list], sheet_schemas[list], validator_plan[list], observability_plan[list], (llm_raw_text/llm_cleaned_json/llm_error optional)
- **AgentTableForAgentArchitect**: job_title, stage_overview[list AgentTableStageOverview], agents[list AgentTableAgentRow]
  - AgentTableStageOverview: stage_id, stage_name, stage_goal
  - AgentTableAgentRow: agent_id/name, stage_stream_step, agent_type(structuring|generator|validator|rag|orchestrator|utility), execution_environment(n8n_gpt_node|http_gpt_api|pure_n8n_logic|human_only), n8n_workflow_id, n8n_node_name, primary_sheet?, rag_enabled: bool, file_search_corpus_hint?, role_and_goal, tasks_covered[list[str]], risks[list[str]], success_metrics[list[str]]
- **AXN8nWorkflow/Node**: workflow_id, name, description, stage_id, nodes[list]; node_id, node_type(trigger|sheets_read|sheets_write|llm|http|function|slack|other), label
- **AXSheetSchema/Column**: sheet_name, description, columns[list]; column(name, type(string|number|boolean|date|json|unknown), required: bool, description)
- **AXValidatorPlanItem**: target(agent_output|sheet_row|workflow), target_id, validation_type(human_review|validator_agent), criteria[list[str]]
- **AXMetricPlanItem**: metric_name, metric_type(counter|gauge|histogram), description, source(workflow|agent|sheet), aggregation(per_run|daily|weekly)
- **AgentSpecsForPromptBuilder** (Stage 5)  
  top-level: `["stage_context","global_policies","agents"]`; fields: stage_context(StageContextForPrompt), global_policies[list[str]], agents[list PromptAgentSpec], llm_* optional  
  - StageContextForPrompt: stage_overview[list AgentTableStageOverview], business_goal?, primary_kpis[list[str]], pain_points[list[str]]  
  - PromptAgentSpec: agent_id/name, stage_stream_step, agent_type, execution_environment, n8n_workflow_id, n8n_node_name, primary_sheet?, rag_enabled: bool, file_search_corpus_hint?, domain_context, role_and_goal, input_schema/output_schema[list AgentIOField], success_metrics[list AgentSuccessMetric], error_policy, validation_policy, notes?
  - AgentIOField: name, type(string|number|boolean|date|json|unknown), required: bool, description, example?
  - AgentSuccessMetric: name, description
- **DeepSkillResearchResult** (Stage 6-A)  
  top-level: `["agent_id","research_focus","research_sections"]`; fields: agent_id, research_focus("skill"|"info+skill"), research_sections(DeepSkillResearchSections: core_skills, thinking_process, frameworks_and_questions, common_pitfalls, good_vs_bad_examples), llm_* optional.
- **SkillCardSet** (Stage 6-B)  
  top-level: `["skill_cards","agent_skill_map"]`; SkillCard(skill_id "S01", skill_name, target_agent_ids, related_task_ids, purpose, when_to_use, core_heuristics, step_checklist, bad_signs, good_signs); AgentSkillMapItem(agent_id, skill_ids); llm_* optional.
- **AgentPromptSet** (Stage 7)  
  top-level: `["summary","agents"]`; AgentPromptBundle(agent_id, execution_environment, single_prompt/system_prompt/user_prompt_template/logic_hint/human_checklist per env, examples[list PromptExample]); PromptExample(example_id, input_example, output_example, notes?); llm_* optional.

## 3) Step 2 – DB 테이블 추가 (`infra/db.py`)
- `ax_workflows`: job_run_id, workflow_name/summary, ax_workflow_mermaid_code, agent_table_json, n8n_workflows_json, sheet_schemas_json, validator_plan_json, observability_plan_json, created_at/updated_at.
- `ax_agents`: job_run_id, agent_id(unique per job), agent_name, stage_stream_step, agent_type, execution_environment, n8n_workflow_id, n8n_node_name, primary_sheet?, rag_enabled(0/1), file_search_corpus_hint?, domain_context, role_and_goal, success_metrics_json, error_policy?, validation_policy?, notes?, agent_spec_json, created_at/updated_at.
- `ax_agent_task_links`: job_run_id, agent_id, task_id, link_type(primary/secondary/validator/observer 등), notes?, created_at/updated_at.
- `ax_deep_research_results`: job_run_id, agent_id, research_focus, research_sections_json, created_at/updated_at.
- `ax_skill_cards`: job_run_id, skill_public_id("S01"...), skill_name, target_agent_ids_json, related_task_ids_json, purpose, when_to_use, core_heuristics_json, step_checklist_json, bad_signs_json, good_signs_json, created_at/updated_at.
- `ax_prompts`: job_run_id, agent_id, execution_environment, prompt_version, single_prompt?, system_prompt?, user_prompt_template?, logic_hint?, human_checklist?, examples_json?, mode?, created_at/updated_at.

## 4) Step 3 – 프롬프트 파일 (`prompts/`)
- 추가/갱신 파일:
  - `ax_workflow_architect.txt` (Stage 4)
  - `ax_agent_architect.txt` (Stage 5)
  - `ax_deep_skill_research.txt` (Stage 6-A)
  - `ax_skill_extractor.txt` (Stage 6-B)
  - `ax_prompt_builder.txt` (Stage 7)
- 공통 규칙: 단일 JSON, 코드블록/불필요 문장 금지, 각 Stage top-level 키 고정(위 Step 1 참조), llm_* 미포함.

## 5) Step 4 – Stage Runner 확장
- Stage name (LLMCallLog.stage_name):
  - `stage4_ax_workflow`
  - `stage5_agent_specs`
  - `stage6_deep_skill_research`
  - `stage6_skill_extractor`
  - `stage7_prompt_builder`
- I/O & 저장:
  1) stage4_ax_workflow  
     - Input: job_meta, WorkflowPlan(2.1) + Mermaid(2.2) 요약, job_tasks/job_task_edges 기반 task_cards.  
     - Call prompt `ax_workflow_architect.txt` → AXWorkflowDesignResult.  
     - Persist: `ax_workflows`; 필요 시 agent_table 기반 초기 `ax_agents`/`ax_agent_task_links` 생성.
  2) stage5_agent_specs  
     - Input: ax_workflows.agent_table_json (+ sheet_schemas).  
     - Call prompt `ax_agent_architect.txt` → AgentSpecsForPromptBuilder.  
     - Persist: upsert into `ax_agents`; 전체 spec은 agent_spec_json에 저장.
  3) stage6_deep_skill_research  
     - For target agent_ids (주로 n8n_gpt_node/http_gpt_api).  
     - Input: job_meta + agent row + 커버 task 목록.  
     - Call prompt `ax_deep_skill_research.txt` → DeepSkillResearchResult.  
     - Persist: `ax_deep_research_results`.
  4) stage6_skill_extractor  
     - Input: job_meta, ax_agents, agent_task_links, ax_deep_research_results.  
     - Call prompt `ax_skill_extractor.txt` → SkillCardSet.  
     - Persist: `ax_skill_cards` (skill_cards, agent_skill_map 반영).
  5) stage7_prompt_builder  
     - Input: AgentSpecsForPromptBuilder, SkillCardSet, global_policies.  
     - Call prompt `ax_prompt_builder.txt` → AgentPromptSet.  
     - Persist: `ax_prompts` per AgentPromptBundle.
- LLM 로그: 기존 `LLMCallLog` 구조 그대로 사용(status/json_parse_error/stub_fallback 등).
- JSON 파싱: `_extract_json_from_text` → `_parse_json_candidates`; 실패 시 llm_error 설정 후 스텁/에러 정책 적용.

## 6) Step 5 – 테스트/기타
- 최소: 스키마 직렬화/파서 단위 테스트, DB upsert 테스트, 스텁 경로에서 파이프라인이 끊기지 않는지 확인.
- 캐시/재실행 정책: job_run_id 기준으로 Stage 4~7도 idempotent upsert 설계.
