"""Repository helpers for AX prompts."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List

from ax_agent_factory.core.schemas.ax import AgentPromptSet
from ax_agent_factory.infra import db


def apply_agent_prompts(job_run_id: int, result: AgentPromptSet) -> None:
    """Upsert AgentPrompt entries into ax_prompts."""
    if not result.agent_prompts:
        return
    conn = db._get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for prompt in result.agent_prompts:
        cur.execute(
            """
            INSERT INTO ax_prompts (
                job_run_id, agent_id, execution_environment, prompt_version,
                single_prompt, system_prompt, user_prompt_template,
                logic_hint, human_checklist, examples_json, mode,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_run_id,
                prompt.agent_id,
                prompt.env,
                prompt.prompt_version,
                None,  # single_prompt optional; mapped below by env
                prompt.system_prompt,
                prompt.user_prompt_template,
                prompt.logic_hint,
                prompt.human_checklist,
                json.dumps(prompt.examples_json, ensure_ascii=False) if prompt.examples_json else None,
                prompt.mode,
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()
