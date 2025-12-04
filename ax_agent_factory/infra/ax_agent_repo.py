"""Repository helpers for AX agents/specs."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from ax_agent_factory.core.schemas.ax import AgentSpec
from ax_agent_factory.infra import db


def apply_agent_specs(job_run_id: int, agent_specs: List[AgentSpec]) -> None:
    """Upsert ax_agents from AgentSpec list."""
    if not agent_specs:
        return
    conn = db._get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for spec in agent_specs:
        stage_stream_step = "/".join([v for v in [spec.stage, spec.stream, spec.step] if v])
        cur.execute(
            """
            INSERT INTO ax_agents (
                job_run_id, agent_id, agent_name, stage_stream_step,
                agent_type, execution_environment, role_and_goal,
                domain_context, success_metrics_json, error_policy, validation_policy,
                notes, agent_spec_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_run_id, agent_id) DO UPDATE SET
                agent_name = excluded.agent_name,
                stage_stream_step = excluded.stage_stream_step,
                agent_type = excluded.agent_type,
                execution_environment = excluded.execution_environment,
                role_and_goal = excluded.role_and_goal,
                domain_context = excluded.domain_context,
                success_metrics_json = excluded.success_metrics_json,
                error_policy = excluded.error_policy,
                validation_policy = excluded.validation_policy,
                notes = excluded.notes,
                agent_spec_json = excluded.agent_spec_json,
                updated_at = excluded.updated_at
            """,
            (
                job_run_id,
                spec.agent_id,
                spec.agent_name,
                stage_stream_step,
                spec.agent_type,
                spec.execution_environment,
                spec.role_and_goal,
                "",  # domain_context not in AgentSpec fields; kept empty placeholder
                json.dumps(spec.success_metrics, ensure_ascii=False),
                json.dumps(spec.error_policy, ensure_ascii=False) if spec.error_policy is not None else None,
                json.dumps(spec.validator_dependencies, ensure_ascii=False),
                spec.notes,
                json.dumps(spec.model_dump(), ensure_ascii=False),
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()


def get_agents(job_run_id: int) -> List[dict]:
    """Fetch ax_agents rows for a job_run."""
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM ax_agents
        WHERE job_run_id = ?
        ORDER BY agent_id
        """,
        (job_run_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
