"""SQLite persistence utilities for AX Agent Factory."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from ax_agent_factory.core.schemas.common import IVCAtomicTask, IVCTask, TaskStaticMeta
from ax_agent_factory.core.schemas.workflow import WorkflowPlan
from ax_agent_factory.models.job_run import JobResearchCollectResult, JobResearchResult, JobRun
from ax_agent_factory.models.llm_log import LLMCallLog

DB_PATH = os.environ.get("AX_DB_PATH", "data/ax_factory.db")


def _ensure_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    _ensure_dir(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_has_column(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def _add_column_if_missing(cur: sqlite3.Cursor, table: str, column: str, ddl: str) -> None:
    if not _table_has_column(cur, table, column):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _ensure_tables() -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            industry_context TEXT,
            business_goal TEXT,
            manual_jd_text TEXT,
            status TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    _add_column_if_missing(cur, "job_runs", "industry_context", "TEXT")
    _add_column_if_missing(cur, "job_runs", "business_goal", "TEXT")
    _add_column_if_missing(cur, "job_runs", "manual_jd_text", "TEXT")
    _add_column_if_missing(cur, "job_runs", "status", "TEXT")
    _add_column_if_missing(cur, "job_runs", "updated_at", "TEXT NOT NULL DEFAULT ''")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_research_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            raw_job_desc TEXT NOT NULL,
            research_sources_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id),
            UNIQUE(job_run_id)
        )
        """
    )
    _add_column_if_missing(cur, "job_research_results", "research_sources_json", "TEXT")
    _add_column_if_missing(cur, "job_research_results", "created_at", "TEXT")
    _add_column_if_missing(cur, "job_research_results", "updated_at", "TEXT")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_research_collect_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            raw_sources_json TEXT NOT NULL,
            job_meta_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id),
            UNIQUE(job_run_id)
        )
        """
    )
    _add_column_if_missing(cur, "job_research_collect_results", "raw_sources_json", "TEXT")
    _add_column_if_missing(cur, "job_research_collect_results", "job_meta_json", "TEXT")
    _add_column_if_missing(cur, "job_research_collect_results", "created_at", "TEXT")
    _add_column_if_missing(cur, "job_research_collect_results", "updated_at", "TEXT")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            task_original_sentence TEXT NOT NULL,
            task_korean TEXT NOT NULL,
            task_english TEXT,
            notes TEXT,
            ivc_phase TEXT,
            ivc_exec_subphase TEXT,
            primitive_lv1 TEXT,
            classification_reason TEXT,
            static_type_lv1 TEXT,
            static_type_lv2 TEXT,
            domain_lv1 TEXT,
            domain_lv2 TEXT,
            rag_required INTEGER,
            rag_reason TEXT,
            value_score INTEGER,
            complexity_score INTEGER,
            value_complexity_quadrant TEXT,
            recommended_execution_env TEXT,
            autoability_reason TEXT,
            data_entities_json TEXT,
            tags_json TEXT,
            stage_id TEXT,
            stream_id TEXT,
            workflow_node_label TEXT,
            is_entry INTEGER,
            is_exit INTEGER,
            is_hub INTEGER,
            review_status TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id),
            UNIQUE(job_run_id, task_id)
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_job_tasks_run ON job_tasks (job_run_id)")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_task_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            source_task_id TEXT NOT NULL,
            target_task_id TEXT NOT NULL,
            label TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_job_task_edges_run_source_target ON job_task_edges (job_run_id, source_task_id, target_task_id)"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            job_run_id INTEGER,
            stage_name TEXT NOT NULL,
            agent_name TEXT,
            model_name TEXT NOT NULL,
            prompt_version TEXT,
            temperature REAL,
            top_p REAL,
            input_payload_json TEXT NOT NULL,
            output_text_raw TEXT,
            output_json_parsed TEXT,
            status TEXT NOT NULL,
            error_type TEXT,
            error_message TEXT,
            latency_ms INTEGER,
            tokens_prompt INTEGER,
            tokens_completion INTEGER,
            tokens_total INTEGER,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_llm_call_logs_job_run ON llm_call_logs (job_run_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_llm_call_logs_stage ON llm_call_logs (stage_name, created_at)"
    )
    # AX extension tables (Stage 4~8)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ax_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            workflow_name TEXT NOT NULL,
            workflow_summary TEXT,
            ax_workflow_mermaid_code TEXT,
            agent_table_json TEXT,
            n8n_workflows_json TEXT,
            sheet_schemas_json TEXT,
            validator_plan_json TEXT,
            observability_plan_json TEXT,
            mode TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ax_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            stage_stream_step TEXT,
            agent_type TEXT,
            execution_environment TEXT,
            n8n_workflow_id TEXT,
            n8n_node_name TEXT,
            primary_sheet TEXT,
            rag_enabled INTEGER,
            file_search_corpus_hint TEXT,
            domain_context TEXT,
            role_and_goal TEXT,
            success_metrics_json TEXT,
            error_policy TEXT,
            validation_policy TEXT,
            notes TEXT,
            agent_spec_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id),
            UNIQUE(job_run_id, agent_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ax_agent_task_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            link_type TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ax_deep_research_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            research_focus TEXT,
            sections_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ax_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            skill_public_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            target_agent_ids_json TEXT,
            related_task_ids_json TEXT,
            purpose TEXT,
            when_to_use TEXT,
            core_heuristics_json TEXT,
            step_checklist_json TEXT,
            bad_signs_json TEXT,
            good_signs_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id),
            UNIQUE(job_run_id, skill_public_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ax_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            execution_environment TEXT,
            prompt_version TEXT,
            single_prompt TEXT,
            system_prompt TEXT,
            user_prompt_template TEXT,
            logic_hint TEXT,
            human_checklist TEXT,
            examples_json TEXT,
            mode TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    conn.commit()
    conn.close()


_ensure_tables()


def set_db_path(path: str) -> None:
    """Override DB path (used for testing) and recreate tables."""
    global DB_PATH
    DB_PATH = path
    _ensure_tables()


def _row_to_job_run(row: sqlite3.Row) -> JobRun:
    updated_at_str = row["updated_at"] if row["updated_at"] else row["created_at"]
    return JobRun(
        id=row["id"],
        company_name=row["company_name"],
        job_title=row["job_title"],
        industry_context=row["industry_context"],
        business_goal=row["business_goal"],
        manual_jd_text=row["manual_jd_text"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(updated_at_str),
    )


def create_or_get_job_run(
    company_name: str,
    job_title: str,
    manual_jd_text: str | None = None,
    *,
    industry_context: str | None = None,
    business_goal: str | None = None,
    status: str | None = None,
) -> JobRun:
    """Return an existing JobRun for same company/job_title/manual_jd_text or create a new one."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM job_runs
        WHERE company_name = ? AND job_title = ? AND IFNULL(manual_jd_text, '') = IFNULL(?, '')
        ORDER BY id DESC
        LIMIT 1
        """,
        (company_name, job_title, manual_jd_text),
    )
    row = cur.fetchone()
    if row:
        conn.close()
        return _row_to_job_run(row)

    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO job_runs (company_name, job_title, industry_context, business_goal, manual_jd_text, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (company_name, job_title, industry_context, business_goal, manual_jd_text, status, now, now),
    )
    conn.commit()
    job_run_id = cur.lastrowid
    cur.execute("SELECT * FROM job_runs WHERE id = ?", (job_run_id,))
    row = cur.fetchone()
    conn.close()
    return _row_to_job_run(row)


def create_job_run(company_name: str, job_title: str) -> JobRun:
    """Insert a new JobRun and return it (legacy helper)."""
    return create_or_get_job_run(company_name, job_title)


def update_job_run_meta(
    job_run_id: int,
    *,
    industry_context: str | None = None,
    business_goal: str | None = None,
    status: str | None = None,
) -> None:
    """Update job_run meta fields."""
    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE job_runs
        SET industry_context = COALESCE(?, industry_context),
            business_goal = COALESCE(?, business_goal),
            status = COALESCE(?, status),
            updated_at = ?
        WHERE id = ?
        """,
        (industry_context, business_goal, status, now, job_run_id),
    )
    conn.commit()
    conn.close()


def get_latest_job_run() -> Optional[JobRun]:
    """Return the most recent JobRun if exists."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_runs ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_job_run(row)


def get_job_run(job_run_id: int) -> Optional[JobRun]:
    """Fetch a JobRun by id."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_runs WHERE id = ?", (job_run_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_job_run(row)


def save_job_research_result(result: JobResearchResult) -> None:
    """Insert or replace a JobResearchResult."""
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    has_legacy_column = _table_has_column(cur, "job_research_results", "research_sources")
    research_sources_json = json.dumps(result.research_sources, ensure_ascii=False)
    cur.execute(
        f"""
        INSERT INTO job_research_results (
            job_run_id,
            raw_job_desc,
            {"research_sources," if has_legacy_column else ""} research_sources_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, {"?," if has_legacy_column else ""} ?, ?, ?)
        ON CONFLICT(job_run_id) DO UPDATE SET
            raw_job_desc = excluded.raw_job_desc,
            {"research_sources = excluded.research_sources," if has_legacy_column else ""}
            research_sources_json = excluded.research_sources_json,
            updated_at = excluded.updated_at
        """,
        (
            result.job_run_id,
            result.raw_job_desc,
            research_sources_json,
            now,
            now,
        )
        if not has_legacy_column
        else (
            result.job_run_id,
            result.raw_job_desc,
            research_sources_json,
            research_sources_json,
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()


def save_job_research_collect_result(result: JobResearchCollectResult) -> None:
    """Insert or replace Stage 0.1 collect result."""
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    has_legacy_column = _table_has_column(cur, "job_research_collect_results", "raw_sources")
    has_job_meta_column = _table_has_column(cur, "job_research_collect_results", "job_meta_json")
    raw_sources_json = json.dumps(result.raw_sources, ensure_ascii=False)
    job_meta_json = json.dumps(result.job_meta or {}, ensure_ascii=False)

    columns = ["job_run_id"]
    values = [result.job_run_id]
    update_parts = []

    if has_legacy_column:
        columns.append("raw_sources")
        values.append(raw_sources_json)
        update_parts.append("raw_sources = excluded.raw_sources")

    columns.append("raw_sources_json")
    values.append(raw_sources_json)
    update_parts.append("raw_sources_json = excluded.raw_sources_json")

    if has_job_meta_column:
        columns.append("job_meta_json")
        values.append(job_meta_json)
        update_parts.append("job_meta_json = excluded.job_meta_json")

    columns.extend(["created_at", "updated_at"])
    values.extend([now, now])
    update_parts.append("updated_at = excluded.updated_at")

    placeholders = ", ".join(["?"] * len(columns))
    cur.execute(
        f"""
        INSERT INTO job_research_collect_results ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(job_run_id) DO UPDATE SET
            {", ".join(update_parts)}
        """,
        tuple(values),
    )
    conn.commit()
    conn.close()


def get_job_research_result(job_run_id: int) -> Optional[JobResearchResult]:
    """Fetch JobResearchResult by job_run_id if exists."""
    conn = _get_conn()
    cur = conn.cursor()
    has_legacy_column = _table_has_column(cur, "job_research_results", "research_sources")
    if has_legacy_column:
        cur.execute(
            """
            SELECT job_run_id, raw_job_desc,
                   COALESCE(research_sources_json, research_sources) AS research_sources_json
            FROM job_research_results
            WHERE job_run_id = ?
            """,
            (job_run_id,),
        )
    else:
        cur.execute(
            """
            SELECT job_run_id, raw_job_desc, research_sources_json
            FROM job_research_results
            WHERE job_run_id = ?
            """,
            (job_run_id,),
        )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return JobResearchResult(
        job_run_id=row["job_run_id"],
        raw_job_desc=row["raw_job_desc"],
        research_sources=json.loads(row["research_sources_json"]),
    )


def get_job_research_collect_result(job_run_id: int) -> Optional[JobResearchCollectResult]:
    """Fetch Stage 0.1 collect result by job_run_id if exists."""
    conn = _get_conn()
    cur = conn.cursor()
    has_legacy_column = _table_has_column(cur, "job_research_collect_results", "raw_sources")
    has_job_meta_column = _table_has_column(cur, "job_research_collect_results", "job_meta_json")
    if has_legacy_column:
        cur.execute(
            """
            SELECT job_run_id,
                   COALESCE(raw_sources_json, raw_sources) AS raw_sources_json
                   {job_meta}
            FROM job_research_collect_results
            WHERE job_run_id = ?
            """.format(
                job_meta=", job_meta_json" if has_job_meta_column else ""
            ),
            (job_run_id,),
        )
    else:
        cur.execute(
            """
            SELECT job_run_id, raw_sources_json {job_meta}
            FROM job_research_collect_results
            WHERE job_run_id = ?
            """.format(
                job_meta=", job_meta_json" if has_job_meta_column else ""
            ),
            (job_run_id,),
        )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    job_meta_json = row["job_meta_json"] if has_job_meta_column else None
    return JobResearchCollectResult(
        job_run_id=row["job_run_id"],
        job_meta=json.loads(job_meta_json) if job_meta_json else None,
        raw_sources=json.loads(row["raw_sources_json"]),
    )


def _ensure_task_row(job_run_id: int, task_id: str, *, conn: Optional[sqlite3.Connection] = None) -> None:
    """Ensure a job_tasks row exists for the given task."""
    owns_conn = conn is None
    connection = conn or _get_conn()
    cur = connection.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT OR IGNORE INTO job_tasks (
            job_run_id, task_id, task_original_sentence, task_korean, task_english, notes,
            created_at, updated_at
        )
        VALUES (?, ?, '', '', NULL, NULL, ?, ?)
        """,
        (job_run_id, task_id, now, now),
    )
    if owns_conn:
        connection.commit()
        connection.close()


def save_task_atoms(job_run_id: int, task_atoms: list[IVCAtomicTask]) -> None:
    """Persist Stage 1-A task atoms into job_tasks (upsert)."""
    if not task_atoms:
        return
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for atom in task_atoms:
        cur.execute(
            """
            INSERT INTO job_tasks (
                job_run_id, task_id, task_original_sentence, task_korean,
                task_english, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_run_id, task_id) DO UPDATE SET
                task_original_sentence = excluded.task_original_sentence,
                task_korean = excluded.task_korean,
                task_english = excluded.task_english,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                job_run_id,
                atom.task_id,
                atom.task_original_sentence,
                atom.task_korean,
                atom.task_english,
                atom.notes,
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()


def apply_ivc_classification(job_run_id: int, ivc_tasks: list[IVCTask]) -> None:
    """Update job_tasks with IVC classification columns."""
    if not ivc_tasks:
        return
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for task in ivc_tasks:
        _ensure_task_row(job_run_id, task.task_id, conn=conn)
        cur.execute(
            """
            UPDATE job_tasks
            SET ivc_phase = ?, ivc_exec_subphase = ?, primitive_lv1 = ?, classification_reason = ?, updated_at = ?
            WHERE job_run_id = ? AND task_id = ?
            """,
            (
                task.ivc_phase,
                task.ivc_exec_subphase,
                task.primitive_lv1,
                task.classification_reason,
                now,
                job_run_id,
                task.task_id,
            ),
        )
    conn.commit()
    conn.close()


def apply_static_classification(job_run_id: int, task_static_meta: list[TaskStaticMeta]) -> None:
    """Update job_tasks with static classification columns."""
    if not task_static_meta:
        return
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for meta in task_static_meta:
        _ensure_task_row(job_run_id, meta.task_id, conn=conn)
        cur.execute(
            """
            UPDATE job_tasks
            SET static_type_lv1 = ?, static_type_lv2 = ?, domain_lv1 = ?, domain_lv2 = ?,
                rag_required = ?, rag_reason = ?, value_score = ?, complexity_score = ?,
                value_complexity_quadrant = ?, recommended_execution_env = ?, autoability_reason = ?,
                data_entities_json = ?, tags_json = ?, updated_at = ?
            WHERE job_run_id = ? AND task_id = ?
            """,
            (
                meta.static_type_lv1,
                meta.static_type_lv2,
                meta.domain_lv1,
                meta.domain_lv2,
                1 if meta.rag_required else 0,
                meta.rag_reason,
                meta.value_score,
                meta.complexity_score,
                meta.value_complexity_quadrant,
                meta.recommended_execution_env,
                meta.autoability_reason,
                json.dumps(meta.data_entities, ensure_ascii=False),
                json.dumps(meta.tags, ensure_ascii=False),
                now,
                job_run_id,
                meta.task_id,
            ),
        )
    conn.commit()
    conn.close()


def apply_workflow_plan(job_run_id: int, plan: WorkflowPlan) -> None:
    """Update job_tasks and job_task_edges with workflow nodes/edges."""
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    for node in plan.nodes:
        node_id = node.node_id if hasattr(node, "node_id") else node.get("node_id")
        label = node.label if hasattr(node, "label") else node.get("label")
        stage_id = node.stage_id if hasattr(node, "stage_id") else node.get("stage_id")
        stream_id = node.stream_id if hasattr(node, "stream_id") else node.get("stream_id")
        is_entry = node.is_entry if hasattr(node, "is_entry") else node.get("is_entry")
        is_exit = node.is_exit if hasattr(node, "is_exit") else node.get("is_exit")
        is_hub = node.is_hub if hasattr(node, "is_hub") else node.get("is_hub")
        _ensure_task_row(job_run_id, node_id, conn=conn)
        cur.execute(
            """
            UPDATE job_tasks
            SET stage_id = ?, stream_id = ?, workflow_node_label = ?, is_entry = ?, is_exit = ?, is_hub = ?, updated_at = ?
            WHERE job_run_id = ? AND task_id = ?
            """,
            (
                stage_id,
                stream_id,
                label,
                1 if is_entry else 0,
                1 if is_exit else 0,
                1 if is_hub else 0,
                now,
                job_run_id,
                node_id,
            ),
        )

    cur.execute("DELETE FROM job_task_edges WHERE job_run_id = ?", (job_run_id,))
    for edge in plan.edges:
        source = edge.source if hasattr(edge, "source") else edge.get("source")
        target = edge.target if hasattr(edge, "target") else edge.get("target")
        label = edge.label if hasattr(edge, "label") else edge.get("label")
        cur.execute(
            """
            INSERT INTO job_task_edges (job_run_id, source_task_id, target_task_id, label, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_run_id, source, target, label, now, now),
        )

    conn.commit()
    conn.close()


def get_job_tasks(job_run_id: int) -> list[dict]:
    """Return all job_tasks rows for a job_run_id."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_tasks WHERE job_run_id = ? ORDER BY task_id", (job_run_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_job_task_edges(job_run_id: int) -> list[dict]:
    """Return all job_task_edges rows for a job_run_id."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_task_edges WHERE job_run_id = ? ORDER BY id", (job_run_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_llm_call_log(log: LLMCallLog | dict) -> Optional[int]:
    """Insert one LLM call log row."""
    if isinstance(log, dict):
        data = log
    else:
        data = log.__dict__

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO llm_call_logs (
            created_at, job_run_id, stage_name, agent_name, model_name,
            prompt_version, temperature, top_p, input_payload_json,
            output_text_raw, output_json_parsed, status, error_type,
            error_message, latency_ms, tokens_prompt, tokens_completion, tokens_total
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("created_at"),
            data.get("job_run_id"),
            data.get("stage_name"),
            data.get("agent_name"),
            data.get("model_name"),
            data.get("prompt_version"),
            data.get("temperature"),
            data.get("top_p"),
            data.get("input_payload_json"),
            data.get("output_text_raw"),
            data.get("output_json_parsed"),
            data.get("status"),
            data.get("error_type"),
            data.get("error_message"),
            data.get("latency_ms"),
            data.get("tokens_prompt"),
            data.get("tokens_completion"),
            data.get("tokens_total"),
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_llm_calls_by_job_run(job_run_id: int) -> list[LLMCallLog]:
    """Return all LLM call logs for a job_run_id, newest first."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM llm_call_logs
        WHERE job_run_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (job_run_id,),
    )
    rows = cur.fetchall()
    conn.close()
    result: list[LLMCallLog] = []
    for row in rows:
        result.append(
            LLMCallLog(
                created_at=row["created_at"],
                job_run_id=row["job_run_id"],
                stage_name=row["stage_name"],
                agent_name=row["agent_name"],
                model_name=row["model_name"],
                prompt_version=row["prompt_version"],
                temperature=row["temperature"],
                top_p=row["top_p"],
                input_payload_json=row["input_payload_json"],
                output_text_raw=row["output_text_raw"],
                output_json_parsed=row["output_json_parsed"],
                status=row["status"],
                error_type=row["error_type"],
                error_message=row["error_message"],
                latency_ms=row["latency_ms"],
                tokens_prompt=row["tokens_prompt"],
                tokens_completion=row["tokens_completion"],
                tokens_total=row["tokens_total"],
            )
        )
    return result
