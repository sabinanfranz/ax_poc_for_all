"""AX layer schemas (Stage 4~8)."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

from ax_agent_factory.core.schemas.common import JobMeta


# ----- Stage 4: AX Workflow Architect -----


class TaskCard(BaseModel):
    task_id: str
    title: str
    phase: str
    one_line_summary: str
    trigger: Optional[str] = None
    inputs: Optional[str] = None
    action: Optional[str] = None
    output: Optional[str] = None
    dna: Optional[dict] = None  # primitive_lv1/domain_lv1 등


class JobAXInputPack(BaseModel):
    job_meta: JobMeta
    workflow_blueprint_mermaid: str
    task_cards: List[TaskCard]


class AgentTableRow(BaseModel):
    stage: str
    stream: Optional[str] = None
    step: Optional[str] = None
    agent_id: str
    agent_name: str
    agent_type: str
    execution_environment: str
    n8n_workflow_id: Optional[str] = None
    n8n_node_name: Optional[str] = None
    primary_sheet: Optional[str] = None
    rag_required: bool
    rag_pattern: str
    role_and_goal: str
    inputs_summary: str
    outputs_summary: str
    human_touchpoint: Optional[str] = None
    risks_summary: Optional[str] = None
    metrics_summary: Optional[str] = None


class AXWorkflowResult(BaseModel):
    ax_workflow_name: str
    ax_workflow_description: str
    mode: str  # "poc" | "advanced"
    mermaid_arch_code: str
    agent_table: List[AgentTableRow]
    validator_layer_json: Optional[dict] = None
    metrics_plan_json: Optional[dict] = None
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


# ----- Stage 5: Agent Architect -----


class AgentIOField(BaseModel):
    name: str
    type: str
    required: bool
    description: str
    example: Optional[str] = None


class AgentSpec(BaseModel):
    agent_id: str
    agent_name: str
    stage: str
    stream: Optional[str] = None
    step: Optional[str] = None
    agent_type: str
    execution_environment: str
    role_and_goal: str
    input_schema: List[AgentIOField]
    output_schema: List[AgentIOField]
    success_metrics: List[str]
    error_policy: Dict | None
    needs_review: bool
    validator_dependencies: List[str]
    notes: Optional[str] = None


class AgentArchitectResult(BaseModel):
    ax_workflow_id: Optional[int] = None
    agent_specs: List[AgentSpec]
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


# ----- Stage 6: Deep Skill Research -----


class DeepSkillResearchSections(BaseModel):
    core_skills: str
    thinking_process: str
    frameworks_and_questions: str
    common_pitfalls: str
    good_vs_bad_examples: str


class DeepSkillResearchResult(BaseModel):
    agent_id: str
    research_focus: str  # "skill" or "info+skill"
    sections: DeepSkillResearchSections
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


class AgentSpecLite(BaseModel):
    agent_id: str
    agent_name: str
    role_and_goal: str
    agent_type: str
    execution_environment: str


class TaskCardLite(BaseModel):
    task_id: str
    title: str
    phase: Optional[str] = None


class DeepSkillResearchInput(BaseModel):
    job_meta: JobMeta
    agent: AgentSpecLite
    tasks: List[TaskCardLite]


# ----- Stage 7: Skill Extractor -----


class SkillCard(BaseModel):
    skill_id: str
    skill_name: str
    target_agent_ids: List[str]
    related_task_ids: List[str]
    purpose: str
    when_to_use: str
    core_heuristics: List[str]
    step_checklist: List[str]
    bad_signs: List[str]
    good_signs: List[str]


class AgentSkillMap(BaseModel):
    agent_id: str
    skill_ids: List[str]


class SkillCardSet(BaseModel):
    skill_cards: List[SkillCard]
    agent_skill_map: List[AgentSkillMap]
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


class SkillExtractorInput(BaseModel):
    job_meta: JobMeta
    agents: List[AgentSpecLite]
    agent_tasks: Dict[str, List[TaskCardLite]]
    deep_research_results: List[DeepSkillResearchResult]


# ----- Stage 8: Prompt Builder -----


class AgentPrompt(BaseModel):
    agent_id: str
    env: str  # n8n_gpt_node | http_gpt_api | pure_n8n_logic | human_only
    prompt_version: str
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    logic_hint: Optional[str] = None
    human_checklist: Optional[str] = None
    examples_json: Optional[List[dict]] = None
    mode: str


class AgentPromptSet(BaseModel):
    agent_prompts: List[AgentPrompt]
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


class PromptBuilderInput(BaseModel):
    job_meta: JobMeta
    agents: List[AgentSpec]
    skills: List[SkillCard]
    global_policies: Optional[dict] = None
