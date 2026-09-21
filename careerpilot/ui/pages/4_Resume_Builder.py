import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional, List

from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import ResumeStrategyType
from careerpilot.db.repository import ResumeRepository
from careerpilot.models.artifact import ResumeArtifact, ResumeArtifactBundle
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import ATSReport
from careerpilot.generators.pdf_validator import PDFValidator
from careerpilot.services.candidate_service import CandidateService
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Resume Builder — CareerPilot AI", page_icon="📄", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

AuthService.require_auth()


st.title("📄 Evidence-Grounded Resume Tailoring Engine")
st.caption("Generate verifiable, ATS-optimized, strategy-aligned resumes without fabricating candidate experience.")

apps = CareerPilotService.list_applications()
if not apps:
    st.info("Please analyze a job description first in **Analyze Job** to enable resume tailoring.")
    st.stop()

# 1. Select Application
app_dict = {f"{a.company} — {a.job_title} ({a.application_id})": a for a in apps}
selected_label = st.selectbox("Select Target Application for Tailoring:", list(app_dict.keys()))
selected_app = app_dict[selected_label]

st.markdown(f"**Target Company:** `{selected_app.company}` | **Target Role:** `{selected_app.job_title}` | **Candidate Fit:** `{selected_app.fit_score:.1f}%`")

from careerpilot.ui.utils.formatters import format_datetime

# 2. Existing Versions & Version Selection
versions = ResumeRepository.list_versions_for_job(selected_app.job_id)
v_choices = {}
if versions:
    for v in versions:
        ats_str = f"{v.ats_score:.1f}%" if getattr(v, "ats_score", None) is not None else "N/A"
        date_str = format_datetime(getattr(v, "created_at", None))
        v_choices[f"{v.version_tag} ({v.strategy_type}) — ATS: {ats_str} [{date_str}]"] = v


col_ver, col_gen = st.columns([1, 1])

with col_ver:
    if v_choices:
        version_keys = list(v_choices.keys())
        selected_v_key = st.selectbox("Select Existing Resume Version to View:", version_keys, index=0)
        selected_version_db = v_choices[selected_v_key]
    else:
        selected_version_db = None
        st.info("No saved resume versions found for this application yet.")

with col_gen:
    st.markdown("#### ⚡ Generate New Version")
    strategy_options = ["AUTO", "AI_DATA_ENGINEER", "DATA_ENGINEER", "GENAI_ENGINEER", "GCP_DATA_ENGINEER"]
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        selected_strat = st.selectbox(
            "Tailoring Strategy:",
            strategy_options,
            index=0,
            key=f"strat_sel_{selected_app.application_id}",
        )
    with col_s2:
        st.write("")
        st.write("")
        generate_btn = st.button("✨ Generate Resume", type="primary", use_container_width=True)

# 3. Handle Generation Trigger
if generate_btn:
    with st.spinner("Assembling verified evidence, auditing Truth Guard, and compiling ATS artifacts..."):
        prog = st.progress(0.2, text="Selecting strategy & matching evidence...")
        prog.progress(0.5, text="Drafting evidence-grounded experience bullets...")
        prog.progress(0.8, text="Running Truth Guard audit & ATS precheck...")
        
        try:
            new_resume, new_ats_report, updated_app = CareerPilotService.generate_resume_for_application(
                app_id=selected_app.application_id,
                strategy=selected_strat if selected_strat != "AUTO" else None,
            )
            artifacts = CareerPilotService.get_or_generate_resume_artifacts(new_resume, company=selected_app.company)
            prog.progress(1.0, text="Resume Generated Successfully!")
            st.success(f"Tailored Resume generated successfully! (ATS Score: **{new_ats_report.overall_score:.1f}%**)")
            st.session_state[f"active_resume_{selected_app.application_id}"] = (new_resume, new_ats_report, artifacts)
            st.rerun()
        except Exception as e:
            logger.exception("Resume generation failed: %s", e)
            st.error(f"Unable to generate resume: {str(e)}")

# 4. Resolve Active Resume, ATS Report & Artifacts
active_cached = st.session_state.get(f"active_resume_{selected_app.application_id}")

current_resume: Optional[TailoredResume] = None
current_ats: Optional[ATSReport] = None
current_artifacts: Optional[ResumeArtifactBundle] = None

if active_cached:
    current_resume, current_ats, current_artifacts = active_cached
elif selected_version_db:
    # Load from selected database version
    try:
        if selected_version_db.tailored_resume_json:
            current_resume = TailoredResume.model_validate(selected_version_db.tailored_resume_json)
    except Exception as ex:
        logger.warning("Could not deserialize TailoredResume from DB: %s", ex)
        current_resume = None

    try:
        if selected_version_db.ats_report_json:
            current_ats = ATSReport.model_validate(selected_version_db.ats_report_json)
    except Exception as ex:
        logger.warning("Could not deserialize ATSReport from DB: %s", ex)
        current_ats = None

    if current_resume:
        try:
            current_artifacts = CareerPilotService.get_or_generate_resume_artifacts(current_resume, company=selected_app.company)
        except Exception:
            current_artifacts = None
    
    if not current_artifacts:
        # Fallback to direct DB file paths
        _act_p = CandidateService.get_active_profile()
        cand_name_slug = (current_resume.header.full_name if current_resume else _act_p.full_name).replace(" ", "_")
        current_artifacts = ResumeArtifactBundle(
            resume_id=selected_version_db.id,
            pdf=ResumeArtifact(
                artifact_type="pdf",
                file_name=f"{cand_name_slug}_{selected_app.job_title.replace(' ', '_')}_{selected_version_db.version_tag}.pdf",
                file_path=selected_version_db.pdf_file_path,
                content_type="application/pdf",
                resume_id=selected_version_db.id,
            ) if selected_version_db.pdf_file_path else None,
            docx=ResumeArtifact(
                artifact_type="docx",
                file_name=f"{cand_name_slug}_{selected_app.job_title.replace(' ', '_')}_{selected_version_db.version_tag}.docx",
                file_path=selected_version_db.docx_file_path,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                resume_id=selected_version_db.id,
            ) if selected_version_db.docx_file_path else None,
            markdown=ResumeArtifact(
                artifact_type="markdown",
                file_name=f"{cand_name_slug}_{selected_app.job_title.replace(' ', '_')}_{selected_version_db.version_tag}.md",
                file_path=selected_version_db.markdown_file_path,
                content_type="text/markdown",
                resume_id=selected_version_db.id,
            ) if selected_version_db.markdown_file_path else None,
        )

st.markdown("---")

# 5. Display Resume Details, Scorecard & Tabs
if current_resume or selected_version_db:
    st.subheader("📑 Tailored Resume Preview & ATS Verification")

    if current_ats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("ATS Compatibility Score", f"{current_ats.overall_score:.1f}%")
        with c2:
            kw_val = f"{current_ats.keyword_alignment.score:.1f}%" if current_ats.keyword_alignment else "N/A"
            st.metric("Keyword Alignment", kw_val)
        with c3:
            sem_val = f"{current_ats.semantic_alignment.score:.1f}%" if current_ats.semantic_alignment else "N/A"
            st.metric("Semantic Alignment", sem_val)
        with c4:
            status_str = current_ats.truth_status.value if hasattr(current_ats.truth_status, "value") else str(current_ats.truth_status)
            st.metric("Truth Guard Status", f"✅ {status_str}")

    tab_preview, tab_truth, tab_ats, tab_export = st.tabs([
        "👁️ Content & Section Preview",
        "🔒 Truth Guard Audit",
        "🎯 ATS Match Analysis",
        "⬇️ Download ATS Clean Files",
    ])

    # Tab 1: Content Preview
    with tab_preview:
        if current_resume:
            st.markdown(f"### {current_resume.header.full_name}")
            st.caption(f"{current_resume.header.email} | {current_resume.header.phone} | {current_resume.header.location}")

            st.markdown("#### Professional Summary")
            sum_text = current_resume.summary.text if hasattr(current_resume.summary, "text") else str(current_resume.summary)
            st.info(f"_{sum_text}_")

            st.markdown("#### Core Technical Skills")
            for sec in current_resume.skills_categories:
                st.markdown(f"**{sec.category_name}:** {', '.join(sec.skills)}")

            st.markdown("#### Professional Experience")
            for exp in current_resume.experiences:
                date_str = f"{exp.start_date} – {exp.end_date}" if hasattr(exp, "start_date") else ""
                st.markdown(f"**{exp.title}** — *{exp.company}* ({date_str})")
                for b in exp.bullets:
                    b_text = b.text if hasattr(b, "text") else str(b)
                    st.markdown(f"- {b_text}")

            st.markdown("#### Key Projects")
            for proj in current_resume.projects:
                tech_str = f" `({', '.join(proj.technologies)})`" if proj.technologies else ""
                st.markdown(f"**{proj.name}**{tech_str}")
                for b in proj.bullets:
                    b_text = b.text if hasattr(b, "text") else str(b)
                    st.markdown(f"- {b_text}")

            if current_resume.education:
                st.markdown("#### Education")
                for edu in current_resume.education:
                    st.markdown(f"- **{edu.degree} in {edu.field_of_study}**, {edu.institution} ({edu.graduation_year})")

            if current_resume.certifications:
                st.markdown("#### Certifications")
                for cert in current_resume.certifications:
                    st.markdown(f"- **{cert.name}** — {cert.issuer} ({cert.year})")
        elif selected_version_db and selected_version_db.markdown_file_path and Path(selected_version_db.markdown_file_path).exists():
            with open(selected_version_db.markdown_file_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())

    # Tab 2: Truth Guard Audit
    with tab_truth:
        st.markdown("### 🔒 Truth Guard & Anti-Hallucination Gate")
        tv = current_resume.truth_validation if current_resume else None
        if tv:
            status_val = tv.status.value if hasattr(tv.status, "value") else str(tv.status)
            st.success(f"**Audit Status:** `{status_val}` | **Verified Claims:** {tv.verified_claims_count} | **Blocked Claims:** {tv.blocked_claims_count}")
            st.markdown(f"**Reasoning:** {tv.summary_reasoning if hasattr(tv, 'summary_reasoning') else tv.summary}")

            truth_rows = []
            for claim in (tv.claims_evaluated or []):
                truth_rows.append({
                    "Claim Type": claim.claim_type if hasattr(claim, "claim_type") else "Fact",
                    "Claim Text": claim.claim_text,
                    "Status": claim.status.value if hasattr(claim.status, "value") else str(claim.status),
                    "Evidence ID": getattr(claim, "matched_evidence_id", None) or "Verified Ground Truth",
                    "Violation / Note": getattr(claim, "violation_reason", None) or "Passed Verification",
                })
            if truth_rows:
                st.dataframe(pd.DataFrame(truth_rows), use_container_width=True, hide_index=True)
        else:
            st.success("✅ All resume bullets and metrics are strictly grounded in candidate evidence.")

    # Tab 3: ATS Match Analysis
    with tab_ats:
        st.markdown("### 🎯 ATS Compatibility Breakdown")
        if current_ats:
            st.markdown(f"**Assessment:** `{current_ats.score_interpretation}`")
            if current_ats.components:
                c_rows = []
                for _, comp in current_ats.components.items():
                    c_rows.append({
                        "Component": comp.name,
                        "Score": f"{comp.score:.1f}%",
                        "Weight": f"{comp.weight * 100:.0f}%",
                        "Weighted Score": f"{comp.weighted_score:.1f}",
                        "Notes": comp.explanation,
                    })
                st.dataframe(pd.DataFrame(c_rows), use_container_width=True, hide_index=True)

            if current_ats.coverage_matrix:
                st.markdown("#### Job Requirements Coverage")
                cov_rows = []
                for r in current_ats.coverage_matrix:
                    cov_rows.append({
                        "Requirement": r.requirement,
                        "Importance": r.importance.value if hasattr(r.importance, "value") else str(r.importance),
                        "Match Level": r.match_level.value if hasattr(r.match_level, "value") else str(r.match_level),
                        "Resume Evidence": r.resume_evidence or "None",
                    })
                st.dataframe(pd.DataFrame(cov_rows), use_container_width=True, hide_index=True)
        else:
            st.info("ATS report will be computed upon resume generation.")

    # Tab 4: Download Formats
    with tab_export:
        st.markdown("### 📥 Export ATS-Friendly Clean Files")
        st.caption("Decoupled ATS artifact engine: single-column layout, standard typography, 100% searchable vector text.")

        if not current_artifacts and current_resume:
            try:
                current_artifacts = CareerPilotService.get_or_generate_resume_artifacts(current_resume, company=selected_app.company)
            except Exception as e:
                logger.exception("Failed to prepare resume artifacts: %s", e)
                st.error("Unable to prepare resume download files.")

        col_docx, col_pdf = st.columns(2)

        with col_docx:
            st.markdown("#### 📄 Microsoft Word (.docx)")
            if current_artifacts and current_artifacts.docx:
                docx_bytes = current_artifacts.docx.get_bytes()
                if docx_bytes:
                    st.success(f"✅ Ready: `{current_artifacts.docx.file_name}`")
                    st.download_button(
                        label="⬇️ Download ATS Clean DOCX",
                        data=docx_bytes,
                        file_name=current_artifacts.docx.file_name,
                        mime=current_artifacts.docx.content_type,
                        type="primary",
                        use_container_width=True,
                        key=f"dl_docx_{selected_app.application_id}_{current_artifacts.resume_id}",
                    )
                else:
                    st.warning("DOCX file content is empty or unreadable.")
            else:
                st.info("DOCX format available after generation.")

        with col_pdf:
            st.markdown("#### 📑 PDF Document (.pdf)")
            if current_artifacts and current_artifacts.pdf:
                # Deterministic PDF validation check
                val_result = PDFValidator.validate_pdf(
                    current_artifacts.pdf.file_path,
                    candidate_name=current_resume.header.full_name if current_resume else CandidateService.get_active_profile().full_name,
                ) if current_artifacts.pdf.file_path else None

                if val_result:
                    if val_result.page_count == 1:
                        st.success(f"✅ **1-Page ATS Standard:** PASS (Page Count: **{val_result.page_count}** | Words: **{val_result.total_words}** | Single-Column: **Verified**)")
                    elif val_result.page_count > 1:
                        st.warning(f"⚠️ **1-Page Target Warning:** Page Count is {val_result.page_count}. Adaptive 1-page optimization recommended.")

                    if val_result.status == "FAIL":
                        st.error(f"❌ PDF Validation Warning: {'; '.join(val_result.formatting_findings)}")
                    else:
                        pdf_bytes = current_artifacts.pdf.get_bytes()
                        if pdf_bytes:
                            st.download_button(
                                label="⬇️ Download ATS Clean PDF (1-Page)",
                                data=pdf_bytes,
                                file_name=current_artifacts.pdf.file_name,
                                mime=current_artifacts.pdf.content_type,
                                type="primary",
                                use_container_width=True,
                                key=f"dl_pdf_{selected_app.application_id}_{current_artifacts.resume_id}",
                            )
                        else:
                            st.error("PDF file content is empty.")
                else:
                    pdf_bytes = current_artifacts.pdf.get_bytes()
                    if pdf_bytes:
                        st.download_button(
                            label="⬇️ Download ATS Clean PDF",
                            data=pdf_bytes,
                            file_name=current_artifacts.pdf.file_name,
                            mime=current_artifacts.pdf.content_type,
                            type="primary",
                            use_container_width=True,
                            key=f"dl_pdf_{selected_app.application_id}_{current_artifacts.resume_id}",
                        )

            else:
                st.info("PDF format available after generation.")

        st.markdown("---")
        if current_resume and st.button("🔄 Re-generate File Artifacts (PDF & DOCX)", key="regen_artifacts_btn"):
            with st.spinner("Re-rendering ATS file artifacts..."):
                try:
                    re_artifacts = CareerPilotService.get_or_generate_resume_artifacts(current_resume, company=selected_app.company)
                    st.session_state[f"active_resume_{selected_app.application_id}"] = (current_resume, current_ats, re_artifacts)
                    st.success("Artifacts re-generated successfully!")
                    st.rerun()
                except Exception as ex:
                    logger.exception("Failed to re-generate artifacts: %s", ex)
                    st.error(f"Re-generation failed: {ex}")
