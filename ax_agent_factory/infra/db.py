"""SQLite persistence utilities for AX Agent Factory."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

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


def _ensure_tables() -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_research_results (
            job_run_id INTEGER PRIMARY KEY,
            raw_job_desc TEXT NOT NULL,
            research_sources TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_research_collect_results (
            job_run_id INTEGER PRIMARY KEY,
            raw_sources TEXT NOT NULL,
            FOREIGN KEY(job_run_id) REFERENCES job_runs(id)
        )
        """
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
    conn.commit()
    conn.close()


_ensure_tables()


def set_db_path(path: str) -> None:
    """Override DB path (used for testing) and recreate tables."""
    global DB_PATH
    DB_PATH = path
    _ensure_tables()


def create_job_run(company_name: str, job_title: str) -> JobRun:
    """Insert a new JobRun and return it."""
    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO job_runs (company_name, job_title, created_at) VALUES (?, ?, ?)",
        (company_name, job_title, now),
    )
    conn.commit()
    job_run_id = cur.lastrowid
    conn.close()
    return JobRun(id=job_run_id, company_name=company_name, job_title=job_title, created_at=datetime.fromisoformat(now))


def get_latest_job_run() -> Optional[JobRun]:
    """Return the most recent JobRun if exists."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_runs ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return JobRun(
        id=row["id"],
        company_name=row["company_name"],
        job_title=row["job_title"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def save_job_research_result(result: JobResearchResult) -> None:
    """Insert or replace a JobResearchResult."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO job_research_results (job_run_id, raw_job_desc, research_sources)
        VALUES (?, ?, ?)
        """,
        (result.job_run_id, result.raw_job_desc, json.dumps(result.research_sources, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def save_job_research_collect_result(result: JobResearchCollectResult) -> None:
    """Insert or replace Stage 0.1 collect result."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO job_research_collect_results (job_run_id, raw_sources)
        VALUES (?, ?)
        """,
        (result.job_run_id, json.dumps(result.raw_sources, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_job_research_result(job_run_id: int) -> Optional[JobResearchResult]:
    """Fetch JobResearchResult by job_run_id if exists."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT job_run_id, raw_job_desc, research_sources FROM job_research_results WHERE job_run_id = ?",
        (job_run_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return JobResearchResult(
        job_run_id=row["job_run_id"],
        raw_job_desc=row["raw_job_desc"],
        research_sources=json.loads(row["research_sources"]),
    )


def get_job_research_collect_result(job_run_id: int) -> Optional[JobResearchCollectResult]:
    """Fetch Stage 0.1 collect result by job_run_id if exists."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT job_run_id, raw_sources FROM job_research_collect_results WHERE job_run_id = ?",
        (job_run_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return JobResearchCollectResult(
        job_run_id=row["job_run_id"],
        raw_sources=json.loads(row["raw_sources"]),
    )


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
