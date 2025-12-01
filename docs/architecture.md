# AX Agent Factory – Architecture

## System Overview
Streamlit frontend orchestrating modular pipelines for research → IVC → DNA → workflow → AX → AgentSpec → Skills → Prompts → Runner. [Update v1.1: Stage 0/1 PoC live with PipelineManager + SQLite + Gemini web_search wrapper; prompts externalized.]

## Pipeline Architecture
Stages 0-9 covering ingestion, research, IVC (A/B/C), DNA (A/B), workflow, AX, AgentSpec, prompts, and runner. [Update v1.1: Stage 0/1 implemented with typed schemas and stubs for missing stages; run_ivc_pipeline links Task Extractor → Phase Classifier.]

## Module & Package Structure
Python packages under `ax_agent_factory` aligned to pipeline stages plus `infra` for shared services. [Update v1.1: core/pipeline_manager.py, core/research.py, core/ivc/{task_extractor,phase_classifier,pipeline}.py; infra/{db,llm_client,prompts}.py; models/{job_run,stages}.py; prompts/*.txt]

## LLM Model Strategy
Provider-agnostic wrapper to swap Gemini/OpenAI; prompt packs per module with safety rails. [Update v1.1: default Gemini model gemini-2.5-flash via env GEMINI_MODEL, web_search tool enabled; stub fallback when key/SDK absent; raw response exposed in UI for debugging.]

## Non-functional Requirements
Scalability via stateless services, observability hooks, and cacheable LLM calls. [Update v1.1: basic logging via UI, stub fallbacks to keep flow alive; SQLite persistence; future: structured logging + tracing.]

## Open Questions / TODO
Pending decisions on storage, evaluation metrics, and human-in-the-loop checkpoints. [Update v1.1: define Stage 2/3 schemas, add retry/robust parsing, persist task_atoms, add auth/secrets management.]
