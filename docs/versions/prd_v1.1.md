# AX Agent Factory – PRD v1.1

## Product Overview
Job2Agent Studio automates from job input to agent delivery. v1.1 reflects the PoC implementation of Stage 0/1 with Streamlit UI, PipelineManager, SQLite persistence, and Gemini integration (web_search). Future stages (2~9) remain planned.

## Target Users & Use Cases
Internal ops/solution engineers who need rapid job-to-agent prototyping; ability to inspect stage outputs in UI and iterate.

## Core Concepts
IVC, DNA, AX architecture, AgentSpec, Skills, Prompts. Stage 0 produces `raw_job_desc` + `research_sources`; Stage 1 produces `task_atoms` → `ivc_tasks` + `phase_summary`.

## End-to-End Flow
0. Job Research (implemented) → 1. IVC (task extract + phase classify, implemented) → 2. DNA → 3. Workflow → 4. Mermaid → 5. AX → 6. AgentSpec → 7. Skill → 8. Prompt → 9. Runner. UI shows per-stage tabs.

## Scope
Included: Streamlit UI, Stage 0/1 pipeline, SQLite CRUD, Gemini web_search wrapper, prompt externalization. Excluded: production auth, monitoring, stages 2~9 logic.

## System Architecture
Streamlit frontend → PipelineManager orchestrates stages; infra: `llm_client` (Gemini), `db` (sqlite), prompts loader; models for JobRun/StageMeta; schemas for IVC. Prompts stored under `ax_agent_factory/prompts`.

## Data Model
JobRun, JobResearchResult(raw_job_desc, research_sources), IVC (task_atoms, ivc_tasks, phase_summary). DB tables: job_runs, job_research_results (sqlite).

## NFR
PoC-grade reliability; fallback to stubs when LLM unavailable; basic error surfacing (UI shows LLM raw/err). Future: retries, logging, metrics, auth/secrets management.

## Roadmap
Next: implement DNA/Workflow stages, persist task_atoms formally, add retries/validation, expand tests, productionize secrets and logging.
