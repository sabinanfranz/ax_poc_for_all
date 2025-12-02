"""Workflow stage schemas (Stage 2.1 structure → 2.2 mermaid)."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """단일 워크플로우 노드(과업)."""

    node_id: str
    label: str
    stage_id: Optional[str] = None
    stream_id: Optional[str] = None
    is_entry: bool = False
    is_exit: bool = False
    is_hub: bool = False
    notes: Optional[str] = None


class WorkflowEdge(BaseModel):
    """노드 간 연결."""

    source: str
    target: str
    label: Optional[str] = None


class WorkflowStage(BaseModel):
    """상위 Stage 그룹."""

    stage_id: str
    name: str
    description: Optional[str] = None


class WorkflowStream(BaseModel):
    """병렬 Stream 그룹."""

    stream_id: str
    name: str
    description: Optional[str] = None
    stage_id: Optional[str] = None


class WorkflowPlan(BaseModel):
    """2.1 워크플로우 구조화 결과."""

    workflow_name: str
    workflow_summary: Optional[str] = None
    stages: List[WorkflowStage] = Field(default_factory=list)
    streams: List[WorkflowStream] = Field(default_factory=list)
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    exit_points: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None


class MermaidDiagram(BaseModel):
    """2.2 Mermaid 렌더링 결과."""

    workflow_name: str
    mermaid_code: str
    warnings: Optional[List[str]] = None
    llm_raw_text: Optional[str] = None
    llm_cleaned_json: Optional[str] = None
    llm_error: Optional[str] = None
