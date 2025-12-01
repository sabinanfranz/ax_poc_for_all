# AX Agent Factory – PRD (latest)

## Product Overview
High-level description of Job2Agent Studio automating research to agent delivery. [Update v1.1: Stage 0/1 PoC implemented in Streamlit with DB + Gemini integration; staging of future stages remains.]

## Target Users & Use Cases
Primary users (ops, solution engineers) and example flows. [TODO: detail personas and scenarios]

## Core Concepts
Key notions: IVC, DNA, AX architecture, AgentSpec, Skills, Prompts. [TODO: expand definitions]

## End-to-End Flow
Stepwise journey from input to sample run. [TODO: map dependencies and milestones]

## Scope
What is in/out for the initial release. [TODO: clarify exclusions and assumptions]

## System Architecture
Logical components and integration points. [Update v1.1: Streamlit UI + PipelineManager + SQLite (infra/db.py); Gemini web_search via infra/llm_client.py; prompts externalized under ax_agent_factory/prompts/.]

## Data Model
Entities for companies, roles, tasks, prompts, runs. [TODO: sketch ERD]

## NFR
Performance, reliability, observability expectations. [TODO: quantify targets]

## Roadmap
Phased delivery with milestones. [Update v1.1: Stage 0/1 PoC done; Stage 2~3 next; full 0~9 integration post-PoC.]
