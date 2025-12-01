# File Structure (v1.1 PoC)

```
ax_agent_factory/
  __init__.py                 # package init
  app.py                      # Streamlit entrypoint (UI)
  core/
    __init__.py
    pipeline_manager.py       # Stage orchestration/caching
    research.py               # Stage 0 Job Research logic (calls llm_client, saves DB)
    ivc/
      __init__.py
      task_extractor.py       # IVC Task Extractor (prompts/ivc_task_extractor.txt)
      phase_classifier.py     # IVC Phase Classifier (prompts/ivc_phase_classifier.txt)
      pipeline.py             # Task Extractor → Phase Classifier pipeline
    dna.py                    # Stage 2 stub
    workflow.py               # Stage 3 stub
  infra/
    __init__.py
    db.py                     # SQLite CRUD (job_runs, job_research_results)
    llm_client.py             # Gemini web_search wrapper, stub fallback
    prompts.py                # Prompt loader (ax_agent_factory/prompts)
  models/
    __init__.py
    job_run.py                # JobRun, JobResearchResult dataclasses
    stages.py                 # Stage metadata (PIPELINE_STAGES)
  prompts/
    __init__.py
    job_research.txt          # Stage 0 prompt
    ivc_task_extractor.txt    # Stage 1 Task Extractor prompt
    ivc_phase_classifier.txt  # Stage 1 Phase Classifier prompt
  tests/
    test_research_stage.py    # Stage 0 save/debug info tests
    test_pipeline_manager.py  # Pipeline cache/IVC invocation tests
    test_ivc_pipeline.py      # IVC pipeline happy/error path tests
  data/
    .gitignore                # placeholder; default DB path (AX_DB_PATH) = data/ax_factory.db
docs/
  prd.md                      # Latest PRD (v1.1)
  versions/prd_v1.1.md        # Archived PRD snapshot
  architecture.md             # System/pipeline architecture
  prompt_guidelines.md        # Prompt rules/storage
  progress.md                 # Work log
  iteration_log.md            # Change log table
  logic_flow.md               # Detailed runtime flow
  README.md                   # Docs index
prompts_reference/            # Legacy prompt references (kept for context)
requirements.txt              # Dependencies (streamlit, pydantic, pytest, google-genai etc.)
.env                          # Environment variables (user-provided, not committed)
data/                         # Default DB location when AX_DB_PATH is unset
```

## Quick Roles
- UI: `app.py` uses `PipelineManager`; tabs per stage, includes LLM raw/error view.
- Orchestration: `core/pipeline_manager.py` routes stages, handles caching.
- Stage 0: `core/research.py` → `infra/llm_client.call_gemini_job_research` → `infra/db.py`.
- Stage 1: `core/ivc/task_extractor.py` + `core/ivc/phase_classifier.py` via `core/ivc/pipeline.py`; prompts in `prompts/`.
- LLM: `infra/llm_client.py` (default model `gemini-2.5-flash`, web_search; stub on missing key/SDK; raw/error attached).
- Prompts: stored under `ax_agent_factory/prompts`, loaded via `infra/prompts.py`.
- DB: SQLite tables job_runs, job_research_results; default path `data/ax_factory.db` unless `AX_DB_PATH` set.
- Tests: under `ax_agent_factory/tests`, mock LLM, verify caching, parsing, and debug info propagation.
