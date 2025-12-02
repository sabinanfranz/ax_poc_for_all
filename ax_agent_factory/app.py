"""Streamlit UI entrypoint for AX Agent Factory PoC."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path when launched via streamlit
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from ax_agent_factory.core.pipeline_manager import PipelineManager
from ax_agent_factory.models.stages import PIPELINE_STAGES
from ax_agent_factory.infra import db
from ax_agent_factory.infra.logging_config import setup_logging


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
        run_stage0 = st.button("0. Job Research 실행")
        run_stage01 = st.button("0~1단계 실행 (Job Research → IVC)")
        run_stage012 = st.button("0~1~2단계 실행 (Job Research → IVC → Workflow)")

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = PipelineManager()
    pipeline: PipelineManager = st.session_state.pipeline

    job_run = st.session_state.get("job_run")
    manual_jd_text_session = st.session_state.get("manual_jd_text")
    job_research_collect_result = st.session_state.get("job_research_collect_result")
    job_research_result = st.session_state.get("job_research_result")
    ivc_result = st.session_state.get("ivc_result")
    workflow_plan = st.session_state.get("workflow_plan")
    workflow_mermaid = st.session_state.get("workflow_mermaid")

    if run_stage0 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(company_name, job_title)
        with st.spinner("0. Job Research 실행 중..."):
            try:
                job_research_result = pipeline.run_stage_0_job_research(
                    job_run,
                    manual_jd_text=manual_jd_text or None,
                    force_rerun=True,
                )
                job_research_collect_result = db.get_job_research_collect_result(job_run.id)
                st.session_state.job_run = job_run
                st.session_state.manual_jd_text = manual_jd_text or None
                st.session_state.job_research_collect_result = job_research_collect_result
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
                job_research_collect_result = db.get_job_research_collect_result(job_run.id)
                ivc_result = pipeline.run_stage_1_ivc(job_run=job_run, job_research_result=job_research_result)
                st.session_state.job_run = job_run
                st.session_state.manual_jd_text = manual_jd_text or None
                st.session_state.job_research_collect_result = job_research_collect_result
                st.session_state.job_research_result = job_research_result
                st.session_state.ivc_result = ivc_result
                st.success("0~1단계 실행 완료!")
            except Exception as exc:  # pragma: no cover - UI feedback
                st.error(f"0~1단계 실행 중 오류 발생: {exc}")

    if run_stage012 and company_name and job_title:
        job_run = pipeline.create_or_get_job_run(company_name, job_title)
        with st.spinner("0~1~2단계 실행 중..."):
            try:
                job_research_result = pipeline.run_stage_0_job_research(
                    job_run,
                    manual_jd_text=manual_jd_text or None,
                    force_rerun=True,
                )
                job_research_collect_result = db.get_job_research_collect_result(job_run.id)
                ivc_result = pipeline.run_stage_1_ivc(job_run=job_run, job_research_result=job_research_result)
                workflow_plan, workflow_mermaid = pipeline.run_stage_3_workflow(
                    job_run=job_run, ivc_result=ivc_result
                )
                st.session_state.job_run = job_run
                st.session_state.manual_jd_text = manual_jd_text or None
                st.session_state.job_research_collect_result = job_research_collect_result
                st.session_state.job_research_result = job_research_result
                st.session_state.ivc_result = ivc_result
                st.session_state.workflow_plan = workflow_plan
                st.session_state.workflow_mermaid = workflow_mermaid
                st.success("0~1~2단계 실행 완료!")
            except Exception as exc:  # pragma: no cover - UI feedback
                st.error(f"0~2단계 실행 중 오류 발생: {exc}")

    implemented_stages = [s for s in PIPELINE_STAGES if s.implemented]
    stage_map = {s.id: s for s in implemented_stages}

    tab_defs: list[tuple[str, str]] = []
    for s in implemented_stages:
        if s.id == "S0_JOB_RESEARCH":
            tab_defs.append(("0.1 Job Research Collect", "S0_JOB_RESEARCH_COLLECT"))
            tab_defs.append(("0.2 Job Research Summarize", "S0_JOB_RESEARCH_SUMMARIZE"))
        elif s.id == "S1_IVC":
            tab_defs.append(("1-A Task Extractor", "S1A_TASK_EXTRACTOR"))
            tab_defs.append(("1-B Phase Classifier", "S1B_PHASE_CLASSIFIER"))
        elif s.id == "S3_WORKFLOW":
            tab_defs.append(("2.1 Workflow Struct", "S2_WORKFLOW_STRUCT"))
            tab_defs.append(("2.2 Workflow Mermaid", "S2_WORKFLOW_MERMAID"))
        else:
            tab_defs.append((s.label, s.id))

    if not tab_defs:
        st.info("아직 구현된 Stage가 없습니다.")
        return

    tabs = st.tabs([label for label, _ in tab_defs])

    for tab, (_, tab_id) in zip(tabs, tab_defs):
        with tab:
            if tab_id == "S0_JOB_RESEARCH_COLLECT":
                st.subheader("0.1 Job Research Collect")
                st.caption(stage_map["S0_JOB_RESEARCH"].description)
                render_stage0_collect_tabs(job_run, job_research_collect_result, manual_jd_text_session)
            elif tab_id == "S0_JOB_RESEARCH_SUMMARIZE":
                st.subheader("0.2 Job Research Summarize")
                st.caption(stage_map["S0_JOB_RESEARCH"].description)
                render_stage0_summarize_tabs(job_run, job_research_result, manual_jd_text_session)
            elif tab_id == "S1A_TASK_EXTRACTOR":
                st.subheader("1-A Task Extractor")
                st.caption(stage_map["S1_IVC"].description)
                render_stage1_task_extractor_tabs(job_run, job_research_result, ivc_result, manual_jd_text_session)
            elif tab_id == "S1B_PHASE_CLASSIFIER":
                st.subheader("1-B Phase Classifier")
                st.caption(stage_map["S1_IVC"].description)
                render_stage1_phase_classifier_tabs(job_run, job_research_result, ivc_result, manual_jd_text_session)
            elif tab_id == "S2_WORKFLOW_STRUCT":
                st.subheader("2.1 Workflow Struct")
                st.caption("Stage 1 결과 기반 워크플로우 구조화")
                render_stage2_workflow_struct_tabs(job_run, ivc_result, workflow_plan)
            elif tab_id == "S2_WORKFLOW_MERMAID":
                st.subheader("2.2 Workflow Mermaid")
                st.caption("워크플로우 구조를 Mermaid 코드로 시각화")
                render_stage2_workflow_mermaid_tabs(job_run, workflow_plan, workflow_mermaid)
            else:
                st.info("이 Stage의 로직은 아직 구현되지 않았습니다.")

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


def render_stage1_task_extractor_tabs(job_run, job_research_result, ivc_result, manual_jd_text: str | None = None) -> None:
    """Render Task Extractor with Stage 0-style flat sub tabs."""
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
                        "industry_context": "",
                        "business_goal": None,
                    },
                    "raw_job_desc": job_research_result.raw_job_desc,
                    "manual_jd_text": manual_jd_text or None,
                }
            )

    # 결과
    with tabs[1]:
        if ivc_result is None:
            st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계 실행을 눌러주세요.")
        else:
            st.subheader("task_atoms")
            if getattr(ivc_result, "task_atoms", None):
                st.json([t.dict() if hasattr(t, "dict") else t for t in ivc_result.task_atoms])
            else:
                st.info("task_atoms가 비어 있습니다. (LLM 스텁 또는 파이프라인 미실행)")

    # LLM 원문
    with tabs[2]:
        llm_raw = getattr(ivc_result, "llm_raw_text", None) if ivc_result else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage1a_llm_raw")
        elif ivc_result:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Task Extractor 결과가 없습니다.")

    # LLM 파싱된 JSON 텍스트
    with tabs[3]:
        cleaned = getattr(ivc_result, "llm_cleaned_json", None) if ivc_result else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage1a_llm_cleaned")
        elif ivc_result:
            st.info("정규화된 JSON 문자열이 없습니다. (LLM 스텁 또는 로깅 미연동)")
            st.json(ivc_result.dict())
        else:
            st.info("아직 Task Extractor 결과가 없습니다.")

    # 에러
    with tabs[4]:
        llm_error = getattr(ivc_result, "llm_error", None) if ivc_result else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif ivc_result:
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
    tabs = st.tabs(["Input", "결과", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

    with tabs[0]:
        if ivc_result is None:
            st.warning("Phase Classifier 입력이 없습니다. Stage 1-A 결과가 필요합니다.")
        else:
            st.json(
                {
                    "job_meta": ivc_result.job_meta.dict() if hasattr(ivc_result, "job_meta") else None,
                    "task_atoms": [t.dict() if hasattr(t, "dict") else t for t in (ivc_result.task_atoms or [])],
                    "manual_jd_text": manual_jd_text or None,
                }
            )

    # 결과
    with tabs[1]:
        if ivc_result is None:
            st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계 실행을 눌러주세요.")
        else:
            st.subheader("ivc_tasks")
            st.json([t.dict() if hasattr(t, "dict") else t for t in ivc_result.ivc_tasks])
            st.subheader("phase_summary")
            st.json(ivc_result.phase_summary.dict())

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


def render_stage2_workflow_struct_tabs(job_run, ivc_result, workflow_plan) -> None:
    """Render Workflow Struct (2.1) tabs."""
    tabs = st.tabs(["Input", "결과", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

    with tabs[0]:
        if job_run is None or ivc_result is None:
            st.warning("Workflow Struct 입력이 없습니다. Stage 1 결과가 필요합니다.")
        else:
            st.json(
                {
                    "job_meta": {
                        "company_name": job_run.company_name,
                        "job_title": job_run.job_title,
                    },
                    "ivc_tasks": [t.dict() if hasattr(t, "dict") else t for t in (ivc_result.ivc_tasks or [])],
                    "task_atoms": [t.dict() if hasattr(t, "dict") else t for t in (ivc_result.task_atoms or [])],
                    "phase_summary": ivc_result.phase_summary.dict() if hasattr(ivc_result, "phase_summary") else None,
                }
            )

    with tabs[1]:
        if workflow_plan is None:
            st.warning("아직 Workflow Struct 결과가 없습니다. 0~1~2 실행을 눌러주세요.")
        else:
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
    tabs = st.tabs(["Input", "결과", "LLM 답변 원문", "LLM 답변 파싱", "에러", "설명", "I/O"])

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
        llm_raw = getattr(workflow_mermaid, "llm_raw_text", None) if workflow_mermaid else None
        if llm_raw:
            st.text_area("LLM raw response", value=llm_raw, height=300, key="stage2_mermaid_llm_raw")
        elif workflow_mermaid:
            st.info("LLM 원문이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Workflow Mermaid 결과가 없습니다.")

    with tabs[3]:
        cleaned = getattr(workflow_mermaid, "llm_cleaned_json", None) if workflow_mermaid else None
        if cleaned:
            st.text_area("정규화된 JSON 문자열", value=cleaned, height=300, key="stage2_mermaid_llm_cleaned")
        elif workflow_mermaid:
            st.info("정규화된 JSON 문자열이 없습니다. (스텁 또는 로깅 미연동)")
        else:
            st.info("아직 Workflow Mermaid 결과가 없습니다.")

    with tabs[4]:
        llm_error = getattr(workflow_mermaid, "llm_error", None) if workflow_mermaid else None
        if llm_error:
            st.error(f"LLM error: {llm_error}")
        elif workflow_mermaid:
            st.success("LLM 에러 없음 (또는 스텁).")
        else:
            st.info("아직 Workflow Mermaid 결과가 없습니다.")

    with tabs[5]:
        st.markdown(
            """
            **Stage 2.2 Mermaid Render 흐름**
            - 입력: WorkflowPlan(2.1 결과)
            - LLM: `infra/llm_client.call_workflow_mermaid`, 프롬프트 `prompts/workflow_mermaid.txt`
            - 출력: mermaid_code, warnings
            """
        )

    with tabs[6]:
        st.markdown(
            """
            **입력**
            - WorkflowPlan(워크플로우 구조)

            **출력**
            - mermaid_code (노션 호환), warnings
            - 디버그: llm_raw_text, llm_cleaned_json, llm_error
            """
        )

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
