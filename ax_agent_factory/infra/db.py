"""SQLite persistence utilities for AX Agent Factory."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from ax_agent_factory.models.job_run import JobResearchResult, JobRun

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
