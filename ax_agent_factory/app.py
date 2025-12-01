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
                render_stage0_tabs(job_run, job_research_result)
            elif stage.id == "S1_IVC":
                render_stage1_tabs(job_run, job_research_result, ivc_result)
            else:
                st.info("이 Stage의 로직은 아직 구현되지 않았습니다.")

    render_log_expander()


def render_stage0_tabs(job_run, job_research_result) -> None:
    """Render Stage 0 run/results and description tabs."""
    run_tab, doc_tab = st.tabs(["실행/결과", "설명/IO"])
    with run_tab:
        if job_research_result is None and job_run is not None:
            job_research_result = db.get_job_research_result(job_run.id)
        if job_research_result is None:
            st.warning("아직 Job Research 결과가 없습니다. 사이드바에서 0단계를 실행하세요.")
            return
        results_tab, llm_tab = st.tabs(["Job Research 결과", "LLM 응답/에러"])
        with results_tab:
            st.subheader("raw_job_desc")
            st.text_area("직무 설명 통합 텍스트", value=job_research_result.raw_job_desc, height=300)
            st.subheader("research_sources")
            st.json(job_research_result.research_sources)
        with llm_tab:
            llm_error = getattr(job_research_result, "llm_error", None)
            llm_raw = getattr(job_research_result, "llm_raw_text", None)
            if llm_error:
                st.error(f"LLM error: {llm_error}")
            if llm_raw:
                st.text_area("LLM raw response", value=llm_raw, height=300)
            if not llm_error and not llm_raw:
                st.info("LLM 원문/에러 정보가 없습니다 (정상 파싱 또는 DB 캐시).")
    with doc_tab:
        st.markdown(
            """
            **Stage 0 흐름**
            - 입력: 회사명, 직무명, (선택) 수동 JD 텍스트
            - LLM: `infra/llm_client.call_gemini_job_research` (모델 기본 `gemini-2.0-flash`, web_search 사용)
              - 프롬프트: `prompts/job_research.txt`
              - 응답 정리: `_clean_json_text` 후 JSON 파싱
            - 출력: `raw_job_desc`, `research_sources[]`
            - 저장/조회: `infra/db.py` (`save_job_research_result`, `get_job_research_result`)
            - 모델: `models/job_run.py` (`JobRun`, `JobResearchResult`)
            - 오케스트레이션: `core/pipeline_manager.py::run_stage_0_job_research`
            """
        )


def render_stage1_tabs(job_run, job_research_result, ivc_result) -> None:
    """Render Stage 1 run/results and description tabs."""
    run_tab, doc_tab = st.tabs(["실행/결과", "설명/IO"])
    with run_tab:
        if ivc_result is None:
            st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계 실행을 눌러주세요.")
            return
        # Task Extractor 결과 (task_atoms)
        st.subheader("Task Extractor → task_atoms")
        if ivc_result.task_atoms:
            st.json([t.dict() if hasattr(t, "dict") else t for t in ivc_result.task_atoms])
        else:
            st.info("task_atoms가 비어 있습니다. (LLM 스텁 또는 파이프라인 미실행)")

        # Phase Classifier 결과
        st.subheader("Phase Classifier → ivc_tasks")
        st.json([t.dict() for t in ivc_result.ivc_tasks])
        st.subheader("phase_summary")
        st.json(ivc_result.phase_summary.dict())
    with doc_tab:
        st.markdown(
            """
            **Stage 1 흐름 (Task Extractor → Phase Classifier)**
            - 입력: Stage 0 `raw_job_desc` + `job_meta` → `core.ivc.pipeline.run_ivc_pipeline`
            - Task Extractor: `core/ivc/task_extractor.py`, 프롬프트 `prompts/ivc_task_extractor.txt`
              - 출력: `task_atoms[]` (JSON)
            - Phase Classifier: `core/ivc/phase_classifier.py`, 프롬프트 `prompts/ivc_phase_classifier.txt`
              - 출력: `ivc_tasks[]`, `phase_summary`
            - 오케스트레이션: `core/ivc/pipeline.py` → `PipelineManager.run_stage_1_ivc`
            """
        )


def render_stage1_tab(job_run, job_research_result, ivc_result) -> None:
    """Render Stage 1 IVC results in the UI."""
    if ivc_result is None:
        st.warning("아직 IVC 결과가 없습니다. 사이드바에서 0~1단계 실행을 눌러주세요.")
        return

    st.subheader("ivc_tasks")
    st.json([t.dict() for t in ivc_result.ivc_tasks])

    st.subheader("phase_summary")
    st.json(ivc_result.phase_summary.dict())


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
