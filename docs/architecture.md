# AX Agent Factory – Architecture

## System Overview
Streamlit frontend orchestrating modular pipelines for research → IVC → DNA → workflow → AX → AgentSpec → Skills → Prompts → Runner. [TODO: finalize orchestration strategy]

## Pipeline Architecture
Stages 0-9 covering ingestion, research, IVC (A/B/C), DNA (A/B), workflow, AX, AgentSpec, prompts, and runner. [TODO: document inputs/outputs per stage]

## Module & Package Structure
Python packages under `app/core` aligned to pipeline stages plus `infra` for shared services. [TODO: add dependency directions]

## LLM Model Strategy
Provider-agnostic wrapper to swap Gemini/OpenAI; prompt packs per module with safety rails. [TODO: list target models and fallback rules]

## Non-functional Requirements
Scalability via stateless services, observability hooks, and cacheable LLM calls. [TODO: capture SLOs and telemetry plan]

## Open Questions / TODO
Pending decisions on storage, evaluation metrics, and human-in-the-loop checkpoints. [TODO: track resolutions]
