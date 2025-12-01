"""Streamlit UI entrypoint for AX Agent Factory PoC."""

from __future__ import annotations

import json
import streamlit as st

from ax_agent_factory.core.pipeline_manager import PipelineManager
from ax_agent_factory.models.stages import PIPELINE_STAGES
from ax_agent_factory.infra import db


st.set_page_config(page_title="AX Agent Factory - PoC", layout="wide")


def main() -> None:
    st.title("AX Agent Factory - PoC")
    st.caption("회사명 + 직무명 → Job Research → IVC/DNA/Workflow ...")

    with st.sidebar:
        company_name = st.text_input("회사명", value="예: A사")
        job_title = st.text_input("직무명", value="예: B2B 교육 컨설턴트")
        manual_jd_text = st.text_area(
            "선택: 직접 붙여넣은 JD 텍스트",
            help="없으면 Gemini가 웹에서 JD/직무 설명을 찾아서 합성합니다.",
        )
        run_stage0 = st.button("0. Job Research 실행")
        run_stage01 = st.button("0~1단계 실행 (Job Research → IVC)")

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = PipelineManager()
    pipeline: PipelineManager = st.session_state.pipeline

    job_run = st.session_state.get("job_run")
    job_research_result = st.session_state.get("job_research_result")
    ivc_result = st.session_state.get("ivc_result")

    if run_stage0 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(company_name, job_title)
        with st.spinner("0. Job Research 실행 중..."):
            try:
                job_research_result = pipeline.run_stage_0_job_research(
                    job_run,
                    manual_jd_text=manual_jd_text or None,
                    force_rerun=True,
                )
                st.session_state.job_run = job_run
                st.session_state.job_research_result = job_research_result
                st.success("Job Research 완료!")
            except Exception as exc:  # pragma: no cover - UI feedback
                st.error(f"Job Research 중 오류 발생: {exc}")

    if run_stage01 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(company_name, job_title)
        with st.spinner("0~1단계 실행 중..."):
            try:
                job_research_result = pipeline.run_stage_0_job_research(
                    job_run,
                    manual_jd_text=manual_jd_text or None,
                    force_rerun=True,
                )
                ivc_result = pipeline.run_stage_1_ivc(job_run=job_run, job_research_result=job_research_result)
                st.session_state.job_run = job_run
                st.session_state.job_research_result = job_research_result
                st.session_state.ivc_result = ivc_result
                st.success("0~1단계 실행 완료!")
            except Exception as exc:  # pragma: no cover - UI feedback
                st.error(f"0~1단계 실행 중 오류 발생: {exc}")

    implemented_stages = [s for s in PIPELINE_STAGES if s.implemented]
    tab_labels = [s.label for s in implemented_stages]
    if not tab_labels:
        st.info("아직 구현된 Stage가 없습니다.")
        return

    tabs = st.tabs(tab_labels)

    for tab, stage in zip(tabs, implemented_stages):
        with tab:
            st.subheader(stage.label)
            st.caption(stage.description)

            if stage.id == "S0_JOB_RESEARCH":
                render_stage0_tab(job_run, job_research_result)
            elif stage.id == "S1_IVC":
                render_stage1_tab(job_run, job_research_result, ivc_result)
            else:
                st.info("이 Stage의 로직은 아직 구현되지 않았습니다.")


def render_stage0_tab(job_run, job_research_result) -> None:
    """Render Stage 0 results in the UI."""
    if job_research_result is None and job_run is not None:
        job_research_result = db.get_job_research_result(job_run.id)

    if job_research_result is None:
        st.warning("아직 Job Research 결과가 없습니다. 사이드바에서 0단계를 실행하세요.")
        return

    st.subheader("raw_job_desc")
    st.text_area("직무 설명 통합 텍스트", value=job_research_result.raw_job_desc, height=300)

    st.subheader("research_sources")
    st.json(job_research_result.research_sources)


def render_stage1_tab(job_run, job_research_result, ivc_result) -> None:
    """Render Stage 1 IVC results in the UI."""
    if ivc_result is None:
        st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계 실행을 눌러주세요.")
        return

    st.subheader("ivc_tasks")
    st.json([t.dict() for t in ivc_result.ivc_tasks])

    st.subheader("phase_summary")
    st.json(ivc_result.phase_summary.dict())


if __name__ == "__main__":
    main()
