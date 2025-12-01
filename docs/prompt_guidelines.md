# AX Agent Factory – Prompt Guidelines

## Global Rules
- Default language: Korean UI, English-friendly outputs when needed.
- Always restate role/goal, expected format, and guardrails in system prompts.
- Enforce JSON/YAML schemas where applicable; return machine-parseable text.
- On errors or ambiguity, ask for clarification with minimal retries.
- [Update v1.1] Prompts stored under `ax_agent_factory/prompts/*.txt` and loaded via `infra/prompts.py`; avoid inline code fences; web_search-aware prompts should request plain JSON without fences.

## Prompt Types
- Job Research: gather company/role signals, sources, and summaries. [v1.1: prompts/job_research.txt]
- IVC: extract tasks, classify phases, format canonical payloads. [v1.1: prompts/ivc_task_extractor.txt, prompts/ivc_phase_classifier.txt]
- DNA: map primitives/domains and mechanisms from tasks.
- Workflow Architect: structure tasks and dependencies; produce Mermaid drafts.
- AX Architect: translate workflows into AX components.
- Agent Architect: turn AX into AgentSpec with tools/memory/IO.
- Skill Planner & Skill Deep Research: enumerate skills and drill down per skill.
- Prompt Builder: compose final prompts per stage.
- Runner/Evaluator: drive sample runs and capture metrics.
- [TODO] Add schema examples and retries per type.

## Versioning & Change Management
- Maintain prompt versions with semantic tags (major/minor/patch).
- Log changes in `docs/iteration_log.md` with rationale and impact.
- Keep prompts under `/prompts` and sync with code expecting their IDs.
- [TODO] Define review/approval workflow before shipping prompt updates.
