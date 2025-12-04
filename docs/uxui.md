# UX/UI Guide
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

## 버튼/실행 흐름
- **다음 단계 실행**: 0.2 → 1.2 → 1.3 → 2.2 순으로 한 단계씩 진행. 이후 재누르면 2.2를 재실행.
- 개별 버튼:
  - `0. Job Research만` (0.1/0.2)
  - `1. IVC까지` (0.x → 1.1/1.2)
  - `1.3 Static까지` (0.x → 1.1/1.2/1.3)
  - `2. Workflow까지` (전체)
- 세션 키: `job_run`, `last_completed_ui_label`, `stage0_collect_result`, `stage0_summarize_result`, `stage1_task_result`, `stage1_phase_result`, `stage1_static_result`, `workflow_plan`, `workflow_mermaid`, `stage4_ax_workflow`, `stage5_agent_specs`, `stage6_deep_research`, `stage7_skill_cards`, `stage8_agent_prompts`.

## Stage 탭 (0.1~2.2)
모든 탭은 동일한 서브탭을 갖는다: `Input` / `결과` / `LLM Raw` / `LLM Cleaned JSON` / `Error` / `설명` / `I/O`.

- **0.1 Collect**: Input(job_run/manual_jd), 결과 raw_sources, LLM 디버그.
- **0.2 Summarize**: Input(job_meta/raw_sources/manual_jd), 결과 raw_job_desc + research_sources, LLM 디버그.
- **1.1 Task Extractor**: Input(job_meta/raw_job_desc), 결과 task_atoms, LLM 디버그.
- **1.2 Phase Classifier**: Input(job_meta/task_atoms), 결과 ivc_tasks + phase_summary, LLM 디버그.
- **1.3 Static Task Classifier**: Input(PhaseClassificationResult dict), 결과 task_static_meta + static_summary, LLM 디버그.
- **2.1 Workflow Struct**: Input(job_meta + ivc_tasks/task_atoms/phase_summary), 결과 stages/streams/nodes/edges/entry/exit/hub, LLM 디버그.
- **2.2 Workflow Mermaid**: Input(workflow_plan), 결과 mermaid_code + warnings, LLM 디버그.

## AX Stage 탭 (4~8)
- 버튼: 사이드바에 4/5/6/7/8 개별 실행 버튼과 `AX 전체 실행(4→8)` 배치.
- 탭: “AX Stages (4~8)” 묶음 탭
  - 4. AX Workflow: Input(job_meta + workflow mermaid 코드 + task_cards), 결과 AXWorkflowResult, LLM Raw/Clean/Error, 설명.
  - 5. Agent Architect: Input(ax_workflow.agent_table), 결과 agent_specs raw, LLM Raw/Clean/Error, 설명.
  - 6. Deep Skill Research: 결과 DeepSkillResearchResult 리스트, LLM Raw/Clean/Error, 설명.
  - 7. Skill Extractor: 결과 SkillCardSet, LLM Raw/Clean/Error, 설명.
  - 8. Prompt Builder: 결과 AgentPromptSet, LLM Raw/Clean/Error, 설명.
- DB 쓰기 요약: 4(ax_workflows/ax_agents), 5(ax_agents upsert), 6(ax_deep_research_docs), 7(ax_skills), 8(ax_prompts).

## 디버깅/로그
- 모든 Stage 결과에 `llm_raw_text`, `llm_cleaned_json`, `llm_error`가 붙어 탭에 그대로 노출.
- `logs/app.log`를 하단 expander에서 tail로 확인.
- DB `llm_call_logs`에 stage_name/status/latency_ms/tokens 기록. 필요 시 sqlite로 조회 가능.
