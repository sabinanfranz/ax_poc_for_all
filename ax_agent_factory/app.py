"""Streamlit UI entrypoint for AX Agent Factory PoC."""

from __future__ import annotations

import sys
from pathlib import Path
import html
import json
from collections import Counter

import streamlit as st
import streamlit.components.v1 as components

# Ensure project root is on sys.path when launched via streamlit
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from ax_agent_factory.core.pipeline_manager import PipelineManager
from ax_agent_factory.core import stage_runner_ax
from ax_agent_factory.models.stages import PIPELINE_STAGES
from ax_agent_factory.infra import db
from ax_agent_factory.infra import ax_workflow_repo, ax_agent_repo, ax_skill_repo
from ax_agent_factory.infra.logging_config import setup_logging
from ax_agent_factory.core.schemas.workflow import MermaidDiagram
from types import SimpleNamespace


st.set_page_config(page_title="AX Agent Factory - PoC", layout="wide")
setup_logging()


def main() -> None:
    st.title("AX Agent Factory - PoC")
    st.caption("회사명 + 직무명 → Job Research → IVC/DNA/Workflow ...")

    with st.sidebar:
        company_name = st.text_input("회사명", value="예: A사")
        job_title = st.text_input("직무명", value="예: B2B 교육 컨설턴트")
        manual_jd_text = st.text_area(
            "선택: 직접 붙여넣은 JD 텍스트",
            help="없으면 Gemini가 웹에서 JD/직무 설명을 찾아서 합성합니다.",
            key="sidebar_manual_jd_text",
        )
        run_stage0 = st.button("0. Job Research만 실행")
        run_stage1 = st.button("1. IVC까지 실행")
        run_stage13 = st.button("1.3 Static까지 실행")
        run_stage2 = st.button("2. Workflow까지 실행")
        run_next = st.button("▶ 다음 단계 실행")
        st.markdown("---")
        run_stage4 = st.button("4. AX Workflow 실행")
        run_stage5 = st.button("5. Agent Architect 실행")
        run_stage6 = st.button("6. Deep Skill Research 실행")
        run_stage7 = st.button("7. Skill Extractor 실행")
        run_stage8 = st.button("8. Prompt Builder 실행")
        run_ax_all = st.button("AX 전체 실행 (4→8)")

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = PipelineManager()
    pipeline: PipelineManager = st.session_state.pipeline

    job_run = st.session_state.get("job_run")
    manual_jd_text_session = st.session_state.get("manual_jd_text")
    stage0_collect_result = st.session_state.get("stage0_collect_result")
    stage0_summarize_result = st.session_state.get("stage0_summarize_result")
    stage1_task_result = st.session_state.get("stage1_task_result")
    stage1_phase_result = st.session_state.get("stage1_phase_result")
    stage1_static_result = st.session_state.get("stage1_static_result")
    workflow_plan = st.session_state.get("workflow_plan")
    workflow_mermaid = st.session_state.get("workflow_mermaid")
    stage4_ax_workflow = st.session_state.get("stage4_ax_workflow")
    stage5_agent_specs = st.session_state.get("stage5_agent_specs")
    stage6_deep_research = st.session_state.get("stage6_deep_research")
    stage7_skill_cards = st.session_state.get("stage7_skill_cards")
    stage8_agent_prompts = st.session_state.get("stage8_agent_prompts")
    last_completed_label = st.session_state.get("last_completed_ui_label")

    def _store_results(results: dict, target_label: str) -> None:
        if "stage0_collect" in results:
            st.session_state.stage0_collect_result = results["stage0_collect"]
        if "stage0_summarize" in results:
            st.session_state.stage0_summarize_result = results["stage0_summarize"]
        if "stage1_task_extract" in results:
            st.session_state.stage1_task_result = results["stage1_task_extract"]
        if "stage1_phase" in results:
            st.session_state.stage1_phase_result = results["stage1_phase"]
        if "stage1_static" in results:
            st.session_state.stage1_static_result = results["stage1_static"]
        if "stage2_plan" in results:
            st.session_state.workflow_plan = results["stage2_plan"]
        if "stage2_mermaid" in results:
            st.session_state.workflow_mermaid = results["stage2_mermaid"]
        if "stage4_ax_workflow" in results:
            st.session_state.stage4_ax_workflow = results["stage4_ax_workflow"]
        if "stage5_agent_specs" in results:
            st.session_state.stage5_agent_specs = results["stage5_agent_specs"]
        if "stage6_deep_research" in results:
            st.session_state.stage6_deep_research = results["stage6_deep_research"]
        if "stage7_skill_cards" in results:
            st.session_state.stage7_skill_cards = results["stage7_skill_cards"]
        if "stage8_agent_prompts" in results:
            st.session_state.stage8_agent_prompts = results["stage8_agent_prompts"]
        st.session_state.last_completed_ui_label = target_label

    def _run_until(target_label: str) -> None:
        nonlocal job_run
        if job_run is None:
            st.warning("JobRun이 없습니다. 먼저 JobRun을 생성/선택하세요.")
            return
        with st.spinner(f"{target_label} 단계까지 실행 중..."):
            try:
                results = pipeline.run_pipeline_until_stage(
                    job_run,
                    target_label,
                    manual_jd_text=manual_jd_text or None,
                )
                _store_results(results, target_label)
                st.success(f"{target_label} 단계까지 실행 완료!")
            except Exception as exc:  # pragma: no cover - UI feedback
                st.error(f"{target_label} 실행 중 오류 발생: {exc}")

    if run_stage0 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(
            company_name, job_title, manual_jd_text=manual_jd_text or None
        )
        st.session_state.job_run = job_run
        st.session_state.manual_jd_text = manual_jd_text or None
        _run_until("0.2")

    if run_stage1 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(
            company_name, job_title, manual_jd_text=manual_jd_text or None
        )
        st.session_state.job_run = job_run
        st.session_state.manual_jd_text = manual_jd_text or None
        _run_until("1.2")

    if run_stage13 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(
            company_name, job_title, manual_jd_text=manual_jd_text or None
        )
        st.session_state.job_run = job_run
        st.session_state.manual_jd_text = manual_jd_text or None
        _run_until("1.3")

    if run_stage2 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(
            company_name, job_title, manual_jd_text=manual_jd_text or None
        )
        st.session_state.job_run = job_run
        st.session_state.manual_jd_text = manual_jd_text or None
        _run_until("2.2")

    if run_next and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(
            company_name, job_title, manual_jd_text=manual_jd_text or None
        )
        st.session_state.job_run = job_run
        st.session_state.manual_jd_text = manual_jd_text or None
        target = PipelineManager.get_next_label(last_completed_label)
        _run_until(target)

    def _ensure_job_run():
        nonlocal job_run
        if job_run is None:
            job_run = pipeline.create_or_get_job_run(
                company_name or "Unknown", job_title or "Unknown", manual_jd_text=manual_jd_text or None
            )
            st.session_state.job_run = job_run
        return job_run

    # AX stage triggers
    if run_stage4:
        jr = _ensure_job_run()
        if jr and workflow_mermaid is None:
            st.warning("Workflow Mermaid 결과가 필요합니다. 먼저 2.2를 실행하세요.")
        else:
            with st.spinner("Stage 4 AX Workflow 실행 중..."):
                result = stage_runner_ax.run_stage4_ax_workflow(
                    jr.id, workflow_mermaid.mermaid_code if workflow_mermaid else ""
                )
                st.session_state.stage4_ax_workflow = result
                st.success("Stage 4 완료")

    if run_stage5:
        jr = _ensure_job_run()
        with st.spinner("Stage 5 Agent Architect 실행 중..."):
            result = stage_runner_ax.run_stage5_agent_architect(jr.id)
            st.session_state.stage5_agent_specs = result
            st.success("Stage 5 완료")

    if run_stage6:
        jr = _ensure_job_run()
        agents_rows = ax_agent_repo.get_agents(jr.id)
        agents_lite = [
            stage_runner_ax.AgentSpecLite(
                agent_id=a["agent_id"],
                agent_name=a["agent_name"],
                role_and_goal=a.get("role_and_goal") or "",
                agent_type=a.get("agent_type") or "",
                execution_environment=a.get("execution_environment") or "",
            )
            for a in agents_rows
        ]
        with st.spinner("Stage 6 Deep Skill Research 실행 중..."):
            result = stage_runner_ax.run_stage6_deep_skill_research(jr.id, agents=agents_lite or None)
            st.session_state.stage6_deep_research = result
            st.success("Stage 6 완료")

    if run_stage7:
        jr = _ensure_job_run()
        agents_rows = ax_agent_repo.get_agents(jr.id)
        agents_lite = [
            stage_runner_ax.AgentSpecLite(
                agent_id=a["agent_id"],
                agent_name=a["agent_name"],
                role_and_goal=a.get("role_and_goal") or "",
                agent_type=a.get("agent_type") or "",
                execution_environment=a.get("execution_environment") or "",
            )
            for a in agents_rows
        ]
        deep_rows = ax_skill_repo.get_deep_research_results(jr.id)
        deep_models = [
            stage_runner_ax.DeepSkillResearchResult(
                agent_id=row["agent_id"],
                research_focus=row.get("research_focus") or "skill",
                sections=json.loads(row["sections_json"]) if row.get("sections_json") else {},
            )
            for row in deep_rows
        ]
        with st.spinner("Stage 7 Skill Extractor 실행 중..."):
            result = stage_runner_ax.run_stage7_skill_extractor(
                jr.id,
                agents=agents_lite or None,
                deep_research_results=deep_models or None,
            )
            st.session_state.stage7_skill_cards = result
            st.success("Stage 7 완료")

    if run_stage8:
        jr = _ensure_job_run()
        with st.spinner("Stage 8 Prompt Builder 실행 중..."):
            result = stage_runner_ax.run_stage8_prompt_builder(jr.id)
            st.session_state.stage8_agent_prompts = result
            st.success("Stage 8 완료")

    if run_ax_all:
        jr = _ensure_job_run()
        if workflow_mermaid is None:
            st.warning("Workflow Mermaid 결과가 필요합니다. 2.2 실행 후 다시 시도하세요.")
        else:
            with st.spinner("AX 전체 실행 중 (4→8)..."):
                stage4 = stage_runner_ax.run_stage4_ax_workflow(jr.id, workflow_mermaid.mermaid_code)
                st.session_state.stage4_ax_workflow = stage4
                stage5 = stage_runner_ax.run_stage5_agent_architect(jr.id)
                st.session_state.stage5_agent_specs = stage5
                agents_rows = ax_agent_repo.get_agents(jr.id)
                agents_lite = [
                    stage_runner_ax.AgentSpecLite(
                        agent_id=a["agent_id"],
                        agent_name=a["agent_name"],
                        role_and_goal=a.get("role_and_goal") or "",
                        agent_type=a.get("agent_type") or "",
                        execution_environment=a.get("execution_environment") or "",
                    )
                    for a in agents_rows
                ]
                stage6 = stage_runner_ax.run_stage6_deep_skill_research(jr.id, agents=agents_lite or None)
                st.session_state.stage6_deep_research = stage6
                deep_rows = ax_skill_repo.get_deep_research_results(jr.id)
                deep_models = [
                    stage_runner_ax.DeepSkillResearchResult(
                        agent_id=row["agent_id"],
                        research_focus=row.get("research_focus") or "skill",
                        sections=json.loads(row["sections_json"]) if row.get("sections_json") else {},
                    )
                    for row in deep_rows
                ]
                stage7 = stage_runner_ax.run_stage7_skill_extractor(
                    jr.id, agents=agents_lite or None, deep_research_results=deep_models or None
                )
                st.session_state.stage7_skill_cards = stage7
                stage8 = stage_runner_ax.run_stage8_prompt_builder(jr.id)
                st.session_state.stage8_agent_prompts = stage8
                st.success("AX 전체 실행 완료")

    implemented_stages = [s for s in PIPELINE_STAGES if s.implemented]
    stage_map = {s.id: s for s in implemented_stages}
    tab_defs: list[tuple[str, str]] = [(s.tab_title, s.id) for s in implemented_stages]

    if not tab_defs:
        st.info("아직 구현된 Stage가 없습니다.")
        return

    tabs = st.tabs([label for label, _ in tab_defs])

    for tab, (_, tab_id) in zip(tabs, tab_defs):
        with tab:
            if tab_id == "S0_1_COLLECT":
                st.subheader("0.1 Job Research Collect")
                st.caption(stage_map["S0_1_COLLECT"].description)
                render_stage0_collect_tabs(job_run, stage0_collect_result, manual_jd_text_session)
            elif tab_id == "S0_2_SUMMARIZE":
                st.subheader("0.2 Job Research Summarize")
                st.caption(stage_map["S0_2_SUMMARIZE"].description)
                render_stage0_summarize_tabs(job_run, stage0_summarize_result, manual_jd_text_session)
            elif tab_id == "S1_1_TASK_EXTRACT":
                st.subheader("1.1 Task Extractor")
                st.caption(stage_map["S1_1_TASK_EXTRACT"].description)
                render_stage1_task_extractor_tabs(
                    job_run, stage0_summarize_result, stage1_task_result, manual_jd_text_session
                )
            elif tab_id == "S1_2_PHASE_CLASSIFY":
                st.subheader("1.2 Phase Classifier")
                st.caption(stage_map["S1_2_PHASE_CLASSIFY"].description)
                render_stage1_phase_classifier_tabs(
                    job_run, stage0_summarize_result, stage1_phase_result, manual_jd_text_session
                )
            elif tab_id == "S1_3_STATIC_CLASSIFY":
                st.subheader("1.3 Static Task Classifier")
                st.caption(stage_map["S1_3_STATIC_CLASSIFY"].description)
                render_stage1_static_classifier_tabs(job_run, stage1_phase_result, stage1_static_result)
            elif tab_id == "S2_1_WORKFLOW_STRUCT":
                st.subheader("2.1 Workflow Struct")
                st.caption(stage_map["S2_1_WORKFLOW_STRUCT"].description)
                render_stage2_workflow_struct_tabs(job_run, stage1_phase_result, workflow_plan)
            elif tab_id == "S2_2_WORKFLOW_MERMAID":
                st.subheader("2.2 Workflow Mermaid")
                st.caption(stage_map["S2_2_WORKFLOW_MERMAID"].description)
                render_stage2_workflow_mermaid_tabs(job_run, workflow_plan, workflow_mermaid)
            else:
                st.info("이 Stage의 로직은 아직 구현되지 않았습니다.")

    st.markdown("---")
    st.subheader("AX Stages (4~8)")
    ax_tabs = st.tabs(
        [
            "4. AX Workflow",
            "5. Agent Architect",
            "6. Deep Skill Research",
            "7. Skill Extractor",
            "8. Prompt Builder",
        ]
    )
    ax_workflow_row = ax_workflow_repo.get_latest_ax_workflow(job_run.id) if job_run else None
    with ax_tabs[0]:
        render_stage4_ax_tabs(job_run, workflow_mermaid, stage4_ax_workflow)
    with ax_tabs[1]:
        render_stage5_agent_tabs(ax_workflow_row, stage5_agent_specs)
    with ax_tabs[2]:
        render_stage6_deep_tabs(stage6_deep_research or [])
    with ax_tabs[3]:
        render_stage7_skill_tabs(stage7_skill_cards)
    with ax_tabs[4]:
        render_stage8_prompt_tabs(stage8_agent_prompts)

    render_log_expander()


def render_stage0_collect_tabs(job_run, job_research_collect_result, manual_jd_text: str | None = None) -> None:
    """Render Stage 0.1 Collect with flat sub-tabs (Input/결과/LLM/파싱/에러/설명/I/O)."""
    if job_research_collect_result is None and job_run is not None:
        job_research_collect_result = db.get_job_research_collect_result(job_run.id)

    tabs = st.tabs(["Input", "결과", "LLM 원문", "LLM 파싱", "에러", "설명", "I/O"])
    with tabs[0]:
        if job_run is None:
            st.warning("JobRun이 없습니다. 사이드바에서 실행하세요.")
        else:
            st.json(
                {
                    "company_name": job_run.company_name,
                    "job_title": job_run.job_title,
                    "manual_jd_text": manual_jd_text or None,
                }
            )
    with tabs[1]:
        if job_research_collect_result is None:
            st.warning("0.1 수집 결과가 없습니다. 사이드바에서 0단계를 실행하세요.")
        else:
            st.subheader("raw_sources")
            st.json(job_research_collect_result.raw_sources)
    with tabs[2]:
        llm_raw = getattr(job_research_collect_result, "llm_raw_text", None) if job_research_collect_result else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage0_collect_llm_raw")
        elif job_research_collect_result:
            st.info("LLM 원문이 없습니다 (정상 파싱/캐시/스텁).")
        else:
            st.info("아직 Job Research Collect 결과가 없습니다.")
    with tabs[3]:
        cleaned = getattr(job_research_collect_result, "llm_cleaned_json", None) if job_research_collect_result else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage0_collect_llm_cleaned")
        elif job_research_collect_result:
            st.info("정규화된 JSON 문자열이 없습니다. (캐시 결과 또는 스텁)")
        else:
            st.info("아직 Job Research Collect 결과가 없습니다.")
    with tabs[4]:
        llm_error = getattr(job_research_collect_result, "llm_error", None) if job_research_collect_result else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif job_research_collect_result:
            st.success("LLM 에러 없음 (또는 캐시 결과).")
        else:
            st.info("아직 Job Research Collect 결과가 없습니다.")
    with tabs[5]:
        st.markdown(
            """
            **Stage 0.1 Web Research Collect**
            - 입력: company_name, job_title, manual_jd_text(optional)
            - 처리: `infra/llm_client.call_job_research_collect` (web_search)
            - 저장: `infra/db.py::save_job_research_collect_result`
            """
        )
    with tabs[6]:
        st.markdown(
            """
            **입력**
            - company_name, job_title, manual_jd_text(optional)

            **출력**
            - raw_sources (url/title/snippet/source_type/score)
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error
            """
        )


def render_stage0_summarize_tabs(job_run, job_research_result, manual_jd_text: str | None = None) -> None:
    """Render Stage 0.2 Summarize with flat sub-tabs (Input/결과/LLM/파싱/에러/설명/I/O)."""
    if job_research_result is None and job_run is not None:
        job_research_result = db.get_job_research_result(job_run.id)
    collect_result = db.get_job_research_collect_result(job_run.id) if job_run else None

    tabs = st.tabs(["Input", "결과", "LLM 원문", "LLM 파싱", "에러", "설명", "I/O"])
    with tabs[0]:
        if job_run is None:
            st.warning("JobRun이 없습니다. 사이드바에서 실행하세요.")
        else:
            st.json(
                {
                    "job_meta": {
                        "company_name": job_run.company_name,
                        "job_title": job_run.job_title,
                    },
                    "raw_sources": collect_result.raw_sources if collect_result else None,
                    "manual_jd_text": manual_jd_text or None,
                }
            )
    with tabs[1]:
        if job_research_result is None:
            st.warning("아직 Job Research Summarize 결과가 없습니다. 사이드바에서 0단계를 실행하세요.")
        else:
            st.subheader("raw_job_desc")
            st.text_area(
                "직무 설명 통합 텍스트",
                value=job_research_result.raw_job_desc,
                height=300,
                key="stage0_summary_raw_desc",
            )
            st.subheader("research_sources")
            st.json(job_research_result.research_sources)
    with tabs[2]:
        llm_raw = getattr(job_research_result, "llm_raw_text", None) if job_research_result else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage0_summary_llm_raw")
        elif job_research_result:
            st.info("LLM 원문이 없습니다 (정상 파싱 또는 DB 캐시).")
        else:
            st.info("아직 Job Research Summarize 결과가 없습니다.")
    with tabs[3]:
        cleaned = getattr(job_research_result, "llm_cleaned_json", None) if job_research_result else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage0_summary_llm_cleaned")
        elif job_research_result:
            st.info("정규화된 JSON 문자열이 없습니다. (캐시 결과 또는 스텁)")
        else:
            st.info("아직 Job Research Summarize 결과가 없습니다.")
    with tabs[4]:
        llm_error = getattr(job_research_result, "llm_error", None) if job_research_result else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif job_research_result:
            st.success("LLM 에러 없음 (또는 캐시 결과).")
        else:
            st.info("아직 Job Research Summarize 결과가 없습니다.")
    with tabs[5]:
        st.markdown(
            """
            **Stage 0.2 Task-Oriented Summarize**
            - 입력: job_meta(company_name, job_title), raw_sources(0.1 결과), manual_jd_text(optional)
            - 처리: `infra/llm_client.call_job_research_summarize`
            - 저장: `infra/db.py::save_job_research_result`
            """
        )
    with tabs[6]:
        st.markdown(
            """
            **입력**
            - job_meta (company_name, job_title)
            - raw_sources (0.1 결과)
            - manual_jd_text(optional)

            **출력**
            - raw_job_desc
            - research_sources
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error
            """
        )


def _db_rows_to_task_atoms(rows: list[dict]) -> list[dict]:
    """Convert job_tasks rows into task_atoms-like dicts."""
    return [
        {
            "task_id": row.get("task_id"),
            "task_original_sentence": row.get("task_original_sentence"),
            "task_korean": row.get("task_korean"),
            "task_english": row.get("task_english"),
            "notes": row.get("notes"),
        }
        for row in rows or []
    ]


def _db_rows_to_ivc_tasks(rows: list[dict]) -> list[dict]:
    """Convert job_tasks rows into ivc_tasks-like dicts."""
    ivc_tasks: list[dict] = []
    for row in rows or []:
        if row.get("ivc_phase"):
            ivc_tasks.append(
                {
                    "task_id": row.get("task_id"),
                    "task_korean": row.get("task_korean"),
                    "task_original_sentence": row.get("task_original_sentence"),
                    "ivc_phase": row.get("ivc_phase"),
                    "ivc_exec_subphase": row.get("ivc_exec_subphase"),
                    "primitive_lv1": row.get("primitive_lv1"),
                    "classification_reason": row.get("classification_reason"),
                }
            )
    return ivc_tasks


def _db_rows_to_phase_summary(rows: list[dict]) -> dict:
    """Build a simple phase_summary-style dict from job_tasks rows."""
    counter: Counter[str] = Counter()
    for row in rows or []:
        phase = row.get("ivc_phase")
        if phase:
            counter[phase] += 1
    return {phase: {"count": count} for phase, count in counter.items()}


def _db_rows_to_static_meta(rows: list[dict]) -> list[dict]:
    """Extract static classification style rows from job_tasks."""
    static_meta: list[dict] = []
    for row in rows or []:
        if any(
            row.get(field)
            for field in [
                "static_type_lv1",
                "static_type_lv2",
                "domain_lv1",
                "domain_lv2",
                "rag_required",
                "recommended_execution_env",
            ]
        ):
            static_meta.append(
                {
                    "task_id": row.get("task_id"),
                    "task_korean": row.get("task_korean"),
                    "static_type_lv1": row.get("static_type_lv1"),
                    "static_type_lv2": row.get("static_type_lv2"),
                    "domain_lv1": row.get("domain_lv1"),
                    "domain_lv2": row.get("domain_lv2"),
                    "rag_required": bool(row.get("rag_required")),
                    "rag_reason": row.get("rag_reason"),
                    "value_score": row.get("value_score"),
                    "complexity_score": row.get("complexity_score"),
                    "value_complexity_quadrant": row.get("value_complexity_quadrant"),
                    "recommended_execution_env": row.get("recommended_execution_env"),
                    "autoability_reason": row.get("autoability_reason"),
                    "data_entities": json.loads(row["data_entities_json"]) if row.get("data_entities_json") else [],
                    "tags": json.loads(row["tags_json"]) if row.get("tags_json") else [],
                }
            )
    return static_meta


def _db_rows_to_static_summary(rows: list[dict]) -> dict:
    """Summarize static meta counts for fallback rendering."""
    counter: Counter[str] = Counter()
    for row in rows or []:
        static_type = row.get("static_type_lv1")
        if static_type:
            counter[static_type] += 1
    if not counter:
        return {}
    return {"static_type_lv1_counts": dict(counter)}


def _load_latest_llm_log(job_run_id: int | None, stage_name: str) -> dict | None:
    """Fetch the latest LLM call log for a stage and job_run_id."""
    if job_run_id is None:
        return None
    calls = db.get_llm_calls_by_job_run(job_run_id)
    for call in calls:
        if call.stage_name == stage_name:
            return call.__dict__
    return None


def render_stage1_task_extractor_tabs(job_run, job_research_result, task_result, manual_jd_text: str | None = None) -> None:
    """Render Task Extractor with Stage 0-style flat sub tabs."""
    # DB fallback if session is empty
    if job_research_result is None and job_run is not None:
        job_research_result = db.get_job_research_result(job_run.id)
    db_task_rows = db.get_job_tasks(job_run.id) if job_run is not None else []
    fallback_task_atoms = _db_rows_to_task_atoms(db_task_rows)
    tabs = st.tabs(["Input", "결과", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

    with tabs[0]:
        if job_run is None or job_research_result is None:
            st.warning("Task Extractor 입력이 없습니다. Stage 0을 먼저 실행하세요.")
        else:
            st.json(
                {
                    "job_meta": {
                        "company_name": job_run.company_name,
                        "job_title": job_run.job_title,
                        "industry_context": job_run.industry_context,
                        "business_goal": job_run.business_goal,
                    },
                    "raw_job_desc": job_research_result.raw_job_desc,
                    "manual_jd_text": manual_jd_text or None,
                }
            )

    # 결과
    with tabs[1]:
        if task_result is None and not fallback_task_atoms:
            st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계를 실행해 주세요.")
        elif task_result is not None:
            st.subheader("task_atoms")
            if getattr(task_result, "task_atoms", None):
                st.json([t.dict() if hasattr(t, "dict") else t for t in task_result.task_atoms])
            else:
                st.info("task_atoms가 비어 있습니다. (LLM 스텁 또는 파이프라인 미실행)")
        else:
            st.info("세션 캐시가 비어 있어 DB에 저장된 task_atoms를 표시합니다.")
            st.json(fallback_task_atoms)

    # LLM 원문
    with tabs[2]:
        llm_raw = getattr(task_result, "llm_raw_text", None) if task_result else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage1a_llm_raw")
        elif task_result:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Task Extractor 결과가 없습니다.")

    # LLM 파싱된 JSON 텍스트
    with tabs[3]:
        cleaned = getattr(task_result, "llm_cleaned_json", None) if task_result else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage1a_llm_cleaned")
        elif task_result:
            st.info("정규화된 JSON 문자열이 없습니다. (LLM 스텁 또는 로깅 미연동)")
            st.json(task_result.dict())
        else:
            st.info("아직 Task Extractor 결과가 없습니다.")

    # 에러
    with tabs[4]:
        llm_error = getattr(task_result, "llm_error", None) if task_result else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif task_result:
            st.success("LLM 에러 없음 (또는 캐시/스텁).")
        else:
            st.info("아직 Task Extractor 결과가 없습니다.")

    # 설명
    with tabs[5]:
        st.markdown(
            """
            **Stage 1-A Task Extractor 흐름**
            - 입력: Stage 0 `raw_job_desc` + `job_meta`
            - LLM: `core/ivc/task_extractor.py`, 프롬프트 `prompts/ivc_task_extractor.txt`
            - 오케스트레이션: `core/ivc/pipeline.py` → `PipelineManager.run_stage_1_ivc`
            - 스텁: LLM 미연동 시 `_stub_result`가 단일 task_atoms를 생성
            """
        )

    # I/O
    with tabs[6]:
        st.markdown(
            """
            **입력**
            - job_meta (company_name, job_title, industry_context, business_goal)
            - raw_job_desc (Stage 0 결과)

            **출력**
            - task_atoms (추출된 원자 과업 리스트)
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error (스텁/미연동 시 미노출)
            """
        )


def render_stage1_phase_classifier_tabs(job_run, job_research_result, ivc_result, manual_jd_text: str | None = None) -> None:
    """Render Phase Classifier with Stage 0-style flat sub tabs."""
    if ivc_result is None and job_run is not None:
        # Try DB fallback: load tasks and show minimal view
        tasks = db.get_job_tasks(job_run.id)
    else:
        tasks = None
    fallback_ivc_tasks = _db_rows_to_ivc_tasks(tasks or [])
    fallback_phase_summary = _db_rows_to_phase_summary(tasks or [])
    fallback_task_atoms = _db_rows_to_task_atoms(tasks or [])
    tabs = st.tabs(["Input", "결과", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

    with tabs[0]:
        if ivc_result is None and not tasks:
            st.warning("Phase Classifier 입력이 없습니다. Stage 1-A 결과가 필요합니다.")
        else:
            task_atoms = (
                [t.dict() if hasattr(t, "dict") else t for t in (ivc_result.task_atoms or [])]
                if ivc_result
                else fallback_task_atoms
            )
            st.json(
                {
                    "job_meta": ivc_result.job_meta.dict() if ivc_result and hasattr(ivc_result, "job_meta") else None,
                    "task_atoms": task_atoms,
                    "manual_jd_text": manual_jd_text or None,
                }
            )

    # 결과
    with tabs[1]:
        if ivc_result is None and not tasks and not fallback_ivc_tasks:
            st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계 실행을 눌러주세요.")
        else:
            st.subheader("ivc_tasks")
            if ivc_result:
                st.json([t.dict() if hasattr(t, "dict") else t for t in ivc_result.ivc_tasks])
                st.subheader("phase_summary")
                st.json(ivc_result.phase_summary.dict())
            elif fallback_ivc_tasks:
                st.info("세션 캐시가 비어 있어 DB에 저장된 IVC 분류 결과를 표시합니다.")
                st.json(fallback_ivc_tasks)
                if fallback_phase_summary:
                    st.subheader("phase_summary (DB)")
                    st.json(fallback_phase_summary)
            else:
                st.info("DB에 저장된 task_atoms만 표시합니다 (ivc_tasks 없음).")

    # LLM 원문
    with tabs[2]:
        llm_raw = getattr(ivc_result, "llm_raw_text", None) if ivc_result else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage1b_llm_raw")
        elif ivc_result:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Phase Classifier 결과가 없습니다.")

    # LLM 파싱된 JSON 텍스트
    with tabs[3]:
        cleaned = getattr(ivc_result, "llm_cleaned_json", None) if ivc_result else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage1b_llm_cleaned")
        elif ivc_result:
            st.info("정규화된 JSON 문자열이 없습니다. (LLM 스텁 또는 로깅 미연동)")
            st.json(ivc_result.dict())
        else:
            st.info("아직 Phase Classifier 결과가 없습니다.")

    # 에러
    with tabs[4]:
        llm_error = getattr(ivc_result, "llm_error", None) if ivc_result else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif ivc_result:
            st.success("LLM 에러 없음 (또는 캐시/스텁).")
        else:
            st.info("아직 Phase Classifier 결과가 없습니다.")

    # 설명
    with tabs[5]:
        st.markdown(
            """
            **Stage 1-B Phase Classifier 흐름**
            - 입력: Task Extractor 결과 `task_atoms[]` + 동일한 `job_meta`
            - LLM: `core/ivc/phase_classifier.py`, 프롬프트 `prompts/ivc_phase_classifier.txt`
            - 오케스트레이션: `core/ivc/pipeline.py` → `PipelineManager.run_stage_1_ivc`
            - 스텁: LLM 미연동 시 모든 태스크를 `P1_SENSE`로 분류하는 `_stub_result`
            """
        )

    # I/O
    with tabs[6]:
        st.markdown(
            """
            **입력**
            - job_meta (company_name, job_title, industry_context, business_goal)
            - task_atoms (Stage 1-A 결과)

            **출력**
            - ivc_tasks (Phase 분류 리스트)
            - phase_summary (Phase별 개수)
            - task_atoms (편의상 재첨부)
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error (스텁/미연동 시 미노출)
            """
        )


def render_stage1_static_classifier_tabs(job_run, phase_result, static_result) -> None:
    """Render Static Task Classifier tabs."""
    tasks = db.get_job_tasks(job_run.id) if job_run is not None else None
    fallback_static_meta = _db_rows_to_static_meta(tasks or [])
    fallback_static_summary = _db_rows_to_static_summary(tasks or [])
    static_log = _load_latest_llm_log(job_run.id if job_run else None, "stage1_static_classifier")
    tabs = st.tabs(["Input", "결과", "LLM Raw", "LLM Cleaned JSON", "Error", "설명", "I/O"])

    with tabs[0]:
        if phase_result is None and not tasks:
            st.warning("Phase Classifier 결과가 없습니다.")
        else:
            st.json(phase_result.dict() if phase_result else {"job_tasks": tasks})

    with tabs[1]:
        if static_result is None and not fallback_static_meta:
            st.warning("Static 결과가 없습니다. 1.3 단계를 실행하세요.")
        elif static_result is not None:
            st.subheader("task_static_meta")
            st.dataframe(
                [
                    {
                        "task_id": t.task_id,
                        "task_korean": t.task_korean,
                        "static_type_lv1": t.static_type_lv1,
                        "domain_lv1": t.domain_lv1,
                        "rag_required": t.rag_required,
                        "value_score": t.value_score,
                        "complexity_score": t.complexity_score,
                        "value_complexity_quadrant": t.value_complexity_quadrant,
                        "recommended_execution_env": t.recommended_execution_env,
                    }
                    for t in static_result.task_static_meta
                ]
            )
            st.subheader("static_summary")
            st.json(static_result.static_summary)
        else:
            st.info("세션 캐시가 비어 있어 DB에 저장된 Static 메타를 표시합니다.")
            st.json(fallback_static_meta)
            if fallback_static_summary:
                st.subheader("static_summary (DB)")
                st.json(fallback_static_summary)

    with tabs[2]:
        llm_raw = getattr(static_result, "llm_raw_text", None) if static_result else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage1_static_llm_raw")
        elif static_log and static_log.get("output_text_raw"):
            st.text_area("LLM raw response (from log)", value=static_log["output_text_raw"], height=300, key="stage1_static_llm_raw_log")
        elif static_result:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Static 결과가 없습니다.")

    with tabs[3]:
        cleaned = getattr(static_result, "llm_cleaned_json", None) if static_result else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage1_static_llm_cleaned")
        elif static_log and static_log.get("output_json_parsed"):
            st.text_area("정규화된 JSON 문자열 (from log)", value=static_log["output_json_parsed"], height=300, key="stage1_static_llm_cleaned_log")
        elif static_result:
            st.info("정규화된 JSON 문자열이 없습니다. (LLM 스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Static 결과가 없습니다.")

    with tabs[4]:
        llm_error = getattr(static_result, "llm_error", None) if static_result else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif static_result:
            st.success("LLM 에러 없음 (또는 캐시/스텁).")
        else:
            st.info("아직 Static 결과가 없습니다.")

    with tabs[5]:
        st.markdown(
            """
            **Stage 1.3 Static Task Classifier 흐름**
            - 입력: Phase Classification 결과 (job_meta/raw_job_desc/task_atoms/ivc_tasks/phase_summary)
            - LLM: prompts/static_task_classifier.txt
            - 출력: task_static_meta (정적 유형/도메인/RAG/가치/복잡도/실행환경)
            """
        )

    with tabs[6]:
        st.markdown(
            """
            **입력**
            - PhaseClassificationResult (job_meta, raw_job_desc, task_atoms, ivc_tasks, phase_summary)

            **출력**
            - task_static_meta, static_summary
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error
            """
        )


def render_stage2_workflow_struct_tabs(job_run, phase_result, workflow_plan) -> None:
    """Render Workflow Struct (2.1) tabs."""
    if workflow_plan is None and job_run is not None:
        workflow_plan = db.get_workflow_plan(job_run.id)
    tasks = db.get_job_tasks(job_run.id) if job_run is not None else None
    edges = db.get_job_task_edges(job_run.id) if job_run is not None else None
    tabs = st.tabs(["Input", "결과", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

    with tabs[0]:
        if job_run is None or (phase_result is None and not tasks):
            st.warning("Workflow Struct 입력이 없습니다. Stage 1 결과가 필요합니다.")
        else:
            st.json(
                {
                    "job_meta": {
                        "company_name": job_run.company_name,
                        "job_title": job_run.job_title,
                    },
                    "ivc_tasks": [t.dict() if hasattr(t, "dict") else t for t in (phase_result.ivc_tasks or [])] if phase_result else None,
                    "task_atoms": [t.dict() if hasattr(t, "dict") else t for t in (phase_result.task_atoms or [])] if phase_result else tasks,
                    "phase_summary": phase_result.phase_summary.dict() if phase_result and hasattr(phase_result, "phase_summary") else None,
                }
            )

    with tabs[1]:
        if workflow_plan is None and not tasks:
            st.warning("아직 Workflow Struct 결과가 없습니다. 0~1~2 실행을 눌러주세요.")
        else:
            if workflow_plan:
                st.subheader("workflow_name")
                st.write(workflow_plan.workflow_name)
                st.subheader("stages")
                st.json([s.dict() for s in workflow_plan.stages])
                st.subheader("streams")
                st.json([s.dict() for s in workflow_plan.streams])
                st.subheader("nodes")
                st.json([n.dict() for n in workflow_plan.nodes])
                st.subheader("edges")
                st.json([e.dict() for e in workflow_plan.edges])
            if tasks:
                st.subheader("job_tasks (DB)")
                st.json(tasks)
            if edges:
                st.subheader("job_task_edges (DB)")
                st.json(edges)

    with tabs[2]:
        llm_raw = getattr(workflow_plan, "llm_raw_text", None) if workflow_plan else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage2_struct_llm_raw")
        elif workflow_plan:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Workflow Struct 결과가 없습니다.")

    with tabs[3]:
        cleaned = getattr(workflow_plan, "llm_cleaned_json", None) if workflow_plan else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage2_struct_llm_cleaned")
        elif workflow_plan:
            st.info("정규화된 JSON 문자열이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Workflow Struct 결과가 없습니다.")

    with tabs[4]:
        llm_error = getattr(workflow_plan, "llm_error", None) if workflow_plan else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif workflow_plan:
            st.success("LLM 에러 없음 (또는 스텁).")
        else:
            st.info("아직 Workflow Struct 결과가 없습니다.")

    with tabs[5]:
        st.markdown(
            """
            **Stage 2.1 Workflow Struct 흐름**
            - 입력: Stage 1 ivc_tasks, task_atoms, phase_summary
            - LLM: `infra/llm_client.call_workflow_struct`, 프롬프트 `prompts/workflow_struct.txt`
            - 출력: WorkflowPlan(stages, streams, nodes, edges, entry/exit)
            """
        )

    with tabs[6]:
        st.markdown(
            """
            **입력**
            - job_meta, task_atoms, ivc_tasks, phase_summary

            **출력**
            - workflow_name, stages, streams, nodes, edges, entry_points, exit_points
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error
            """
        )


def render_stage2_workflow_mermaid_tabs(job_run, workflow_plan, workflow_mermaid) -> None:
    """Render Workflow Mermaid (2.2) tabs."""
    mermaid_log = _load_latest_llm_log(job_run.id if job_run else None, "stage2_workflow_mermaid")
    if workflow_plan is None and job_run is not None:
        workflow_plan = db.get_workflow_plan(job_run.id)
    if workflow_mermaid is None and job_run is not None:
        workflow_mermaid = db.get_workflow_mermaid_result(job_run.id)
    if workflow_mermaid is None and mermaid_log and mermaid_log.get("output_json_parsed"):
        try:
            parsed = json.loads(mermaid_log["output_json_parsed"])
            workflow_mermaid = MermaidDiagram(**parsed)
            workflow_mermaid.llm_raw_text = mermaid_log.get("output_text_raw")  # type: ignore[attr-defined]
            workflow_mermaid.llm_cleaned_json = mermaid_log.get("output_json_parsed")  # type: ignore[attr-defined]
        except Exception:
            pass
    tabs = st.tabs(["Input", "결과", "Mermaid 미리보기", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

    with tabs[0]:
        if workflow_plan is None:
            st.warning("Workflow Mermaid 입력이 없습니다. 2.1 결과가 필요합니다.")
        else:
            st.json(workflow_plan.dict())

    with tabs[1]:
        if workflow_mermaid is None:
            st.warning("아직 Workflow Mermaid 결과가 없습니다. 0~1~2 실행을 눌러주세요.")
        else:
            st.subheader("mermaid_code")
            st.code(workflow_mermaid.mermaid_code, language="mermaid")
            if workflow_mermaid.warnings:
                st.subheader("warnings")
                st.json(workflow_mermaid.warnings)

    with tabs[2]:
        if workflow_mermaid is None:
            st.warning("아직 Workflow Mermaid 결과가 없습니다.")
        else:
            st.subheader("Mermaid 렌더링")
            render_mermaid_chart(workflow_mermaid.mermaid_code)

    with tabs[3]:
        llm_raw = getattr(workflow_mermaid, "llm_raw_text", None) if workflow_mermaid else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage2_mermaid_llm_raw")
        elif workflow_mermaid:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Workflow Mermaid 결과가 없습니다.")

    with tabs[4]:
        cleaned = getattr(workflow_mermaid, "llm_cleaned_json", None) if workflow_mermaid else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage2_mermaid_llm_cleaned")
        elif workflow_mermaid:
            st.info("정규화된 JSON 문자열이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Workflow Mermaid 결과가 없습니다.")

    with tabs[5]:
        llm_error = getattr(workflow_mermaid, "llm_error", None) if workflow_mermaid else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif workflow_mermaid:
            st.success("LLM 에러 없음 (또는 스텁).")
        else:
            st.info("아직 Workflow Mermaid 결과가 없습니다.")

    with tabs[6]:
        st.markdown(
            """
            **Stage 2.2 Mermaid Render 흐름**
            - 입력: WorkflowPlan(2.1 결과)
            - LLM: `infra/llm_client.call_workflow_mermaid`, 프롬프트 `prompts/workflow_mermaid.txt`
            - 출력: mermaid_code, warnings
            """
        )

    with tabs[7]:
        st.markdown(
            """
            **입력**
            - WorkflowPlan(워크플로우 구조)

            **출력**
            - mermaid_code (노션 호환), warnings
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error
            """
        )


def render_stage4_ax_tabs(job_run, workflow_mermaid, ax_result) -> None:
    tabs = st.tabs(["Input", "결과", "LLM 원문", "LLM 파싱", "에러", "설명"])
    with tabs[0]:
        if job_run is None:
            st.warning("JobRun이 없습니다.")
        else:
            st.json(
                {
                    "job_meta": {
                        "company_name": job_run.company_name,
                        "job_title": job_run.job_title,
                        "industry_context": job_run.industry_context,
                        "business_goal": job_run.business_goal,
                    },
                    "workflow_mermaid_code": getattr(workflow_mermaid, "mermaid_code", None),
                }
            )
    with tabs[1]:
        if ax_result is None:
            st.info("Stage 4 결과가 없습니다.")
        else:
            st.subheader("AX Workflow")
            st.json(ax_result.model_dump() if hasattr(ax_result, "model_dump") else ax_result)
    with tabs[2]:
        raw = getattr(ax_result, "llm_raw_text", None) if ax_result else None
        st.text_area("LLM raw", value=raw or "", height=260)
    with tabs[3]:
        cleaned = getattr(ax_result, "llm_cleaned_json", None) if ax_result else None
        st.text_area("LLM cleaned JSON", value=cleaned or "", height=260)
    with tabs[4]:
        err = getattr(ax_result, "llm_error", None) if ax_result else None
        st.text(err or "LLM 에러 없음")
    with tabs[5]:
        st.markdown(
            """
            - 입력: job_meta + workflow mermaid + task_cards(DB job_tasks)
            - 출력: AXWorkflowResult (ax_workflows/ax_agents 저장)
            """
        )


def render_stage5_agent_tabs(ax_workflow_row, agent_specs) -> None:
    tabs = st.tabs(["Input", "결과", "LLM 원문", "LLM 파싱", "에러", "설명"])
    with tabs[0]:
        st.json({"agent_table": ax_workflow_row.get("agent_table") if ax_workflow_row else []})
    with tabs[1]:
        if agent_specs is None:
            st.info("Stage 5 결과가 없습니다.")
        else:
            st.json(agent_specs)
    with tabs[2]:
        raw = agent_specs.get("llm_raw_text") if isinstance(agent_specs, dict) else None
        st.text_area("LLM raw", value=raw or "", height=260)
    with tabs[3]:
        cleaned = agent_specs.get("llm_cleaned_json") if isinstance(agent_specs, dict) else None
        st.text_area("LLM cleaned JSON", value=cleaned or "", height=260)
    with tabs[4]:
        err = agent_specs.get("llm_error") if isinstance(agent_specs, dict) else None
        st.text(err or "LLM 에러 없음")
    with tabs[5]:
        st.markdown(
            """
            - 입력: ax_workflows.agent_table_json
            - 출력: AgentSpecs (ax_agents에 반영)
            """
        )


def render_stage6_deep_tabs(deep_results) -> None:
    tabs = st.tabs(["결과", "LLM 원문", "LLM 파싱", "에러", "설명"])
    with tabs[0]:
        if not deep_results:
            st.info("Stage 6 결과가 없습니다.")
        else:
            st.json([r.model_dump() if hasattr(r, "model_dump") else r for r in deep_results])
    with tabs[1]:
        raw = deep_results[0].llm_raw_text if deep_results and hasattr(deep_results[0], "llm_raw_text") else None
        st.text_area("LLM raw", value=raw or "", height=260)
    with tabs[2]:
        cleaned = deep_results[0].llm_cleaned_json if deep_results and hasattr(deep_results[0], "llm_cleaned_json") else None
        st.text_area("LLM cleaned JSON", value=cleaned or "", height=260)
    with tabs[3]:
        err = deep_results[0].llm_error if deep_results and hasattr(deep_results[0], "llm_error") else None
        st.text(err or "LLM 에러 없음")
    with tabs[4]:
        st.markdown(
            """
            - 입력: job_meta + agent + task_cards
            - 출력: DeepSkillResearchResult (ax_deep_research_docs 저장)
            """
        )


def render_stage7_skill_tabs(skill_result) -> None:
    tabs = st.tabs(["결과", "LLM 원문", "LLM 파싱", "에러", "설명"])
    with tabs[0]:
        if skill_result is None:
            st.info("Stage 7 결과가 없습니다.")
        else:
            st.json(skill_result.model_dump() if hasattr(skill_result, "model_dump") else skill_result)
    with tabs[1]:
        raw = getattr(skill_result, "llm_raw_text", None) if skill_result else None
        st.text_area("LLM raw", value=raw or "", height=260)
    with tabs[2]:
        cleaned = getattr(skill_result, "llm_cleaned_json", None) if skill_result else None
        st.text_area("LLM cleaned JSON", value=cleaned or "", height=260)
    with tabs[3]:
        err = getattr(skill_result, "llm_error", None) if skill_result else None
        st.text(err or "LLM 에러 없음")
    with tabs[4]:
        st.markdown(
            """
            - 입력: job_meta + agents + agent_tasks + deep_research_results
            - 출력: SkillCardSet (ax_skills 저장)
            """
        )


def render_stage8_prompt_tabs(prompt_result) -> None:
    tabs = st.tabs(["결과", "LLM 원문", "LLM 파싱", "에러", "설명"])
    with tabs[0]:
        if prompt_result is None:
            st.info("Stage 8 결과가 없습니다.")
        else:
            st.json(prompt_result.model_dump() if hasattr(prompt_result, "model_dump") else prompt_result)
    with tabs[1]:
        raw = getattr(prompt_result, "llm_raw_text", None) if prompt_result else None
        st.text_area("LLM raw", value=raw or "", height=260)
    with tabs[2]:
        cleaned = getattr(prompt_result, "llm_cleaned_json", None) if prompt_result else None
        st.text_area("LLM cleaned JSON", value=cleaned or "", height=260)
    with tabs[3]:
        err = getattr(prompt_result, "llm_error", None) if prompt_result else None
        st.text(err or "LLM 에러 없음")
    with tabs[4]:
        st.markdown(
            """
            - 입력: job_meta + agent_specs + skill_cards (+global_policies)
            - 출력: AgentPromptSet (ax_prompts 저장)
            """
        )
def render_mermaid_chart(mermaid_code: str, height: int = 600) -> None:
    """Embed Mermaid code as a rendered chart using a lightweight client-side script."""
    escaped = html.escape(mermaid_code)
    html_content = f"""
    <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
      </head>
      <body>
        <div class="mermaid">
        {escaped}
        </div>
        <script>
          mermaid.initialize({{ startOnLoad: true }});
        </script>
      </body>
    </html>
    """
    components.html(html_content, height=height, scrolling=True)


def render_log_expander() -> None:
    """Show tail of logs/app.log for quick debugging."""
    log_path = Path("logs/app.log")
    if not log_path.exists():
        return
    try:
        with log_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
        with st.expander("logs/app.log (tail)"):
            st.text("".join(lines))
    except Exception:
        # UI should not break due to log file access issues
        pass


if __name__ == "__main__":
    main()
