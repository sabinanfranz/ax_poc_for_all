"""Repository helpers for AX skills and deep research."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List

from ax_agent_factory.core.schemas.ax import (
    DeepSkillResearchResult,
    SkillCard,
    SkillCardSet,
)
from ax_agent_factory.infra import db


def save_deep_research_result(job_run_id: int, result: DeepSkillResearchResult) -> None:
    """Insert one deep research doc row."""
    conn = db._get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO ax_deep_research_docs (
            job_run_id, agent_id, research_focus, sections_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            job_run_id,
            result.agent_id,
            result.research_focus,
            json.dumps(result.sections.model_dump(), ensure_ascii=False),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()


def get_deep_research_results(job_run_id: int) -> List[dict]:
    """Fetch deep research docs for a job_run."""
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM ax_deep_research_docs
        WHERE job_run_id = ?
        ORDER BY id
        """,
        (job_run_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_skill_cards(job_run_id: int) -> List[dict]:
    """Fetch skill cards for a job_run."""
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM ax_skills
        WHERE job_run_id = ?
        ORDER BY skill_public_id
        """,
        (job_run_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def apply_skill_cards(job_run_id: int, result: SkillCardSet) -> None:
    """Upsert skill cards into ax_skills."""
    if not result.skill_cards:
        return
    conn = db._get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for card in result.skill_cards:
        cur.execute(
            """
            INSERT INTO ax_skills (
                job_run_id, skill_public_id, skill_name, target_agent_ids_json, related_task_ids_json,
                purpose, when_to_use, core_heuristics_json, step_checklist_json, bad_signs_json, good_signs_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_run_id, skill_public_id) DO UPDATE SET
                skill_name = excluded.skill_name,
                target_agent_ids_json = excluded.target_agent_ids_json,
                related_task_ids_json = excluded.related_task_ids_json,
                purpose = excluded.purpose,
                when_to_use = excluded.when_to_use,
                core_heuristics_json = excluded.core_heuristics_json,
                step_checklist_json = excluded.step_checklist_json,
                bad_signs_json = excluded.bad_signs_json,
                good_signs_json = excluded.good_signs_json,
                updated_at = excluded.updated_at
            """,
            (
                job_run_id,
                card.skill_id,
                card.skill_name,
                json.dumps(card.target_agent_ids, ensure_ascii=False),
                json.dumps(card.related_task_ids, ensure_ascii=False),
                card.purpose,
                card.when_to_use,
                json.dumps(card.core_heuristics, ensure_ascii=False),
                json.dumps(card.step_checklist, ensure_ascii=False),
                json.dumps(card.bad_signs, ensure_ascii=False),
                json.dumps(card.good_signs, ensure_ascii=False),
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()
