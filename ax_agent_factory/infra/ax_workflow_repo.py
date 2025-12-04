"""Repository helpers for AX workflow outputs."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List

from ax_agent_factory.core.schemas.ax import AgentTableRow, AXWorkflowResult
from ax_agent_factory.infra import db


def upsert_ax_workflow(job_run_id: int, result: AXWorkflowResult) -> int:
    """Insert or update ax_workflows row. Returns ax_workflows.id."""
    conn = db._get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    agent_table_json = json.dumps([row.model_dump() for row in result.agent_table], ensure_ascii=False)
    cur.execute(
        """
        SELECT id FROM ax_workflows
        WHERE job_run_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (job_run_id,),
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE ax_workflows
            SET workflow_name = ?, workflow_summary = ?, ax_workflow_mermaid_code = ?,
                agent_table_json = ?, validator_plan_json = ?, observability_plan_json = ?,
                mode = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                result.ax_workflow_name,
                result.ax_workflow_description,
                result.mermaid_arch_code,
                agent_table_json,
                json.dumps(result.validator_layer_json, ensure_ascii=False)
                if result.validator_layer_json is not None
                else None,
                json.dumps(result.metrics_plan_json, ensure_ascii=False)
                if result.metrics_plan_json is not None
                else None,
                result.mode,
                now,
                row["id"],
            ),
        )
        conn.commit()
        conn.close()
        return row["id"]

    cur.execute(
        """
        INSERT INTO ax_workflows (
            job_run_id, workflow_name, workflow_summary, ax_workflow_mermaid_code,
            agent_table_json, validator_plan_json, observability_plan_json, mode,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_run_id,
            result.ax_workflow_name,
            result.ax_workflow_description,
            result.mermaid_arch_code,
            agent_table_json,
            json.dumps(result.validator_layer_json, ensure_ascii=False)
            if result.validator_layer_json is not None
            else None,
            json.dumps(result.metrics_plan_json, ensure_ascii=False)
            if result.metrics_plan_json is not None
            else None,
            result.mode,
            now,
            now,
        ),
    )
    conn.commit()
    workflow_id = cur.lastrowid
    conn.close()
    return workflow_id


def get_latest_ax_workflow(job_run_id: int) -> dict | None:
    """Return latest ax_workflows row as dict (JSON fields parsed)."""
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM ax_workflows
        WHERE job_run_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (job_run_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        **dict(row),
        "agent_table": json.loads(row["agent_table_json"]) if row["agent_table_json"] else [],
        "validator_plan": json.loads(row["validator_plan_json"]) if row["validator_plan_json"] else None,
        "observability_plan": json.loads(row["observability_plan_json"]) if row["observability_plan_json"] else None,
        "n8n_workflows": json.loads(row["n8n_workflows_json"]) if row["n8n_workflows_json"] else None,
        "sheet_schemas": json.loads(row["sheet_schemas_json"]) if row["sheet_schemas_json"] else None,
    }


def sync_ax_agents_from_agent_table(job_run_id: int, ax_workflow_id: int, agent_rows: List[AgentTableRow]) -> None:
    """Upsert ax_agents rows based on agent_table output."""
    conn = db._get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for row in agent_rows:
        stage_stream_step = "/".join([v for v in [row.stage, row.stream, row.step] if v])
        cur.execute(
            """
            INSERT INTO ax_agents (
                job_run_id, agent_id, agent_name, stage_stream_step,
                agent_type, execution_environment, n8n_workflow_id, n8n_node_name,
                primary_sheet, rag_enabled, file_search_corpus_hint, role_and_goal,
                success_metrics_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_run_id, agent_id) DO UPDATE SET
                agent_name = excluded.agent_name,
                stage_stream_step = excluded.stage_stream_step,
                agent_type = excluded.agent_type,
                execution_environment = excluded.execution_environment,
                n8n_workflow_id = excluded.n8n_workflow_id,
                n8n_node_name = excluded.n8n_node_name,
                primary_sheet = excluded.primary_sheet,
                rag_enabled = excluded.rag_enabled,
                file_search_corpus_hint = excluded.file_search_corpus_hint,
                role_and_goal = excluded.role_and_goal,
                success_metrics_json = excluded.success_metrics_json,
                updated_at = excluded.updated_at
            """,
            (
                job_run_id,
                row.agent_id,
                row.agent_name,
                stage_stream_step,
                row.agent_type,
                row.execution_environment,
                row.n8n_workflow_id,
                row.n8n_node_name,
                row.primary_sheet,
                1 if row.rag_required else 0,
                row.rag_pattern,
                row.role_and_goal,
                json.dumps([], ensure_ascii=False),
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()
