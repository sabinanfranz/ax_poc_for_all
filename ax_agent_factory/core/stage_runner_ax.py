"""Stage 4~8 runner stubs for AX layer."""

from __future__ import annotations

import json
from typing import List, Optional

from ax_agent_factory.core.schemas.ax import (
    AgentPromptSet,
    AgentSpec,
    AgentSpecLite,
    AgentTableRow,
    AXWorkflowResult,
    DeepSkillResearchInput,
    DeepSkillResearchResult,
    JobAXInputPack,
    PromptBuilderInput,
    SkillCard,
    SkillCardSet,
    SkillExtractorInput,
    TaskCard,
    TaskCardLite,
)
from ax_agent_factory.core.schemas.common import JobMeta
from ax_agent_factory.infra import (
    ax_agent_repo,
    ax_prompt_repo,
    ax_skill_repo,
    ax_workflow_repo,
    db,
    llm_client,
)


def _build_job_meta(job_run) -> JobMeta:
    return JobMeta(
        company_name=job_run.company_name,
        job_title=job_run.job_title,
        industry_context=job_run.industry_context,
        business_goal=job_run.business_goal,
    )


def _load_task_cards(job_run_id: int) -> List[TaskCard]:
    cards: List[TaskCard] = []
    for row in db.get_job_tasks(job_run_id):
        title = row.get("task_korean") or row.get("workflow_node_label") or row.get("task_id")
        cards.append(
            TaskCard(
                task_id=row["task_id"],
                title=title or "",
                phase=row.get("primitive_lv1") or row.get("ivc_phase") or "",
                one_line_summary=row.get("task_original_sentence", "")[:120],
                trigger=None,
                inputs=None,
                action=None,
                output=None,
                dna={
                    "ivc_phase": row.get("ivc_phase"),
                    "primitive_lv1": row.get("primitive_lv1"),
                    "static_type_lv1": row.get("static_type_lv1"),
                    "domain_lv1": row.get("domain_lv1"),
                },
            )
        )
    return cards


def run_stage4_ax_workflow(job_run_id: int, workflow_mermaid_code: str = "") -> AXWorkflowResult:
    job_run = db.get_job_run(job_run_id)
    if job_run is None:
        raise ValueError("job_run not found")
    job_meta = _build_job_meta(job_run)
    task_cards = _load_task_cards(job_run_id)
    input_pack = JobAXInputPack(
        job_meta=job_meta,
        workflow_blueprint_mermaid=workflow_mermaid_code,
        task_cards=task_cards,
    )
    output = llm_client.call_ax_workflow_architect(input_pack, job_run_id=job_run_id)
    result = AXWorkflowResult(**output)
    ax_workflow_id = ax_workflow_repo.upsert_ax_workflow(job_run_id, result)
    ax_workflow_repo.sync_ax_agents_from_agent_table(job_run_id, ax_workflow_id, result.agent_table)
    return result


def run_stage5_agent_architect(job_run_id: int, payload: Optional[dict] = None) -> dict:
    """
    Build payload from latest AX workflow agent_table if available, call LLM, and upsert agent specs.
    """
    if payload is None:
        wf = ax_workflow_repo.get_latest_ax_workflow(job_run_id)
        payload = {
            "agent_table": wf.get("agent_table") if wf else [],
            "job_run_id": job_run_id,
        }
    output = llm_client.call_agent_architect(payload, job_run_id=job_run_id)
    try:
        from ax_agent_factory.core.schemas.ax import AgentArchitectResult

        parsed = AgentArchitectResult(**output)
        ax_agent_repo.apply_agent_specs(job_run_id, parsed.agent_specs)
    except Exception:
        # leave raw output for debugging
        pass
    return output


def run_stage6_deep_skill_research(job_run_id: int, agents: Optional[List[AgentSpecLite]] = None) -> List[DeepSkillResearchResult]:
    job_run = db.get_job_run(job_run_id)
    if job_run is None:
        raise ValueError("job_run not found")
    job_meta = _build_job_meta(job_run)
    if agents is None:
        agent_rows = ax_agent_repo.get_agents(job_run_id)
        agents = [
            AgentSpecLite(
                agent_id=row["agent_id"],
                agent_name=row["agent_name"],
                role_and_goal=row.get("role_and_goal", ""),
                agent_type=row.get("agent_type", ""),
                execution_environment=row.get("execution_environment", ""),
            )
            for row in agent_rows
        ]
    results: List[DeepSkillResearchResult] = []
    tasks = _load_task_cards(job_run_id)
    task_lite = [TaskCardLite(task_id=t.task_id, title=t.title, phase=t.phase) for t in tasks]
    for agent in agents:
        payload = DeepSkillResearchInput(job_meta=job_meta, agent=agent, tasks=task_lite)
        output = llm_client.call_deep_skill_research(payload, job_run_id=job_run_id)
        parsed = DeepSkillResearchResult(**output)
        ax_skill_repo.save_deep_research_result(job_run_id, parsed)
        results.append(parsed)
    return results


def run_stage7_skill_extractor(
    job_run_id: int,
    agents: Optional[List[AgentSpecLite]] = None,
    deep_research_results: Optional[List[DeepSkillResearchResult]] = None,
) -> SkillCardSet:
    job_run = db.get_job_run(job_run_id)
    if job_run is None:
        raise ValueError("job_run not found")
    job_meta = _build_job_meta(job_run)
    tasks = _load_task_cards(job_run_id)
    task_lite = [TaskCardLite(task_id=t.task_id, title=t.title, phase=t.phase) for t in tasks]
    if agents is None:
        agent_rows = ax_agent_repo.get_agents(job_run_id)
        agents = [
            AgentSpecLite(
                agent_id=row["agent_id"],
                agent_name=row["agent_name"],
                role_and_goal=row.get("role_and_goal", ""),
                agent_type=row.get("agent_type", ""),
                execution_environment=row.get("execution_environment", ""),
            )
            for row in agent_rows
        ]
    if deep_research_results is None:
        deep_rows = ax_skill_repo.get_deep_research_results(job_run_id)
        deep_research_results = [
            DeepSkillResearchResult(
                agent_id=row["agent_id"],
                research_focus=row.get("research_focus") or "skill",
                sections=json.loads(row["sections_json"]) if row.get("sections_json") else {},
            )
            for row in deep_rows
        ]
    agent_tasks = {a.agent_id: task_lite for a in agents} if agents else {}
    payload = SkillExtractorInput(
        job_meta=job_meta,
        agents=agents or [],
        agent_tasks=agent_tasks,
        deep_research_results=deep_research_results or [],
    )
    output = llm_client.call_skill_extractor(json.loads(payload.model_dump_json(ensure_ascii=False)), job_run_id=job_run_id)
    result = SkillCardSet(**output)
    ax_skill_repo.apply_skill_cards(job_run_id, result)
    return result


def run_stage8_prompt_builder(
    job_run_id: int,
    agents_payload: Optional[List[dict]] = None,
    skills_payload: Optional[List[dict]] = None,
    global_policies: Optional[dict] = None,
) -> AgentPromptSet:
    job_run = db.get_job_run(job_run_id)
    if job_run is None:
        raise ValueError("job_run not found")
    job_meta = _build_job_meta(job_run)
    if agents_payload is None:
        agent_rows = ax_agent_repo.get_agents(job_run_id)
        agents_payload = [
            json.loads(row["agent_spec_json"]) if row.get("agent_spec_json") else row for row in agent_rows
        ]
    if skills_payload is None:
        skills_payload = ax_skill_repo.get_skill_cards(job_run_id)
    from ax_agent_factory.core.schemas.ax import AgentSpec, AgentPromptSet, SkillCard

    agents = [AgentSpec(**a) if not isinstance(a, AgentSpec) else a for a in agents_payload]
    skills = [SkillCard(**s) if not isinstance(s, SkillCard) else s for s in skills_payload]
    pb_input = PromptBuilderInput(job_meta=job_meta, agents=agents, skills=skills, global_policies=global_policies)
    output = llm_client.call_prompt_builder(pb_input, job_run_id=job_run_id)
    result = AgentPromptSet(**output)
    ax_prompt_repo.apply_agent_prompts(job_run_id, result)
    return result
