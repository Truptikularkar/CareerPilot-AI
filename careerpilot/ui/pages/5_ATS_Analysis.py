import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import pandas as pd
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.db.repository import ResumeRepository

st.set_page_config(page_title="ATS Analysis — CareerPilot AI", page_icon="🎯", layout="wide")

from careerpilot.services.auth_service import AuthService

AuthService.require_auth()


st.title("🎯 ATS Compatibility & Resume Scoring Engine")
st.caption("Explainable, deterministic ATS-style compatibility analysis, keyword alignment, and formatting verification.")

apps = CareerPilotService.list_applications()
if not apps:
    st.info("Please analyze a job description and generate a resume first.")
    st.stop()

# 1. Select Application & Version
c_app, c_ver = st.columns([2, 1])
with c_app:
    app_dict = {f"{a.company} — {a.job_title} ({a.application_id})": a for a in apps}
    selected_label = st.selectbox("Select Target Application:", list(app_dict.keys()))
    selected_app = app_dict[selected_label]

with c_ver:
    versions = ResumeRepository.list_versions_for_job(selected_app.job_id)
    if versions:
        v_dict = {f"{v.version_tag} ({v.strategy_type}) - ATS: {v.ats_score:.1f}%": v for v in versions}
        selected_v_label = st.selectbox("Select Resume Version:", list(v_dict.keys()))
        selected_v = v_dict[selected_v_label]
    else:
        selected_v = None

if not selected_v and not selected_app.resume_id:
    st.warning("No tailored resume found for this application. Please generate one in **Resume Builder**.")
    st.stop()

# 2. Fetch ATS Report
with st.spinner("Loading ATS Compatibility Report..."):
    ats_report = CareerPilotService.evaluate_ats_for_application(
        selected_app.application_id,
        resume_id=selected_v.id if selected_v else None
    )

st.markdown("---")

# 3. Overall Scorecard
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    st.metric("ATS Compatibility Score", f"{ats_report.overall_score:.1f}%")
with sc2:
    st.metric("Must-Have Match", ats_report.must_have_coverage_ratio)
with sc3:
    st.metric("Nice-To-Have Match", ats_report.nice_to_have_coverage_ratio)
with sc4:
    st.metric("Truth Guard Status", ats_report.truth_status.value if hasattr(ats_report.truth_status, "value") else str(ats_report.truth_status))

st.markdown(f"**ATS Assessment:** `{ats_report.score_interpretation}`")

if ats_report.overall_score >= 70:
    st.success("✅ **Your resume contains most of the important skills from this JD.**")
elif ats_report.overall_score >= 50:
    st.info("ℹ️ **Your resume contains some relevant skills, but is missing important keywords from this JD.**")
else:
    st.warning("⚠️ **Your resume has low keyword coverage for this specific role.**")

st.markdown("---")

# 4. Dimension Breakdown
st.subheader("📊 Component Scoring Breakdown")
COMP_FRIENDLY_NAMES = {
    "Keyword & Requirement Coverage": "JD Keyword Match",
    "Skill Taxonomy Alignment": "Skill Category Match",
    "Semantic Role Alignment": "Role Positioning Match",
    "Experience & Seniority Alignment": "Experience Level Match",
    "Resume Structure & Completeness": "Resume Structure & Sections",
    "ATS Formatting & Single-Column Compliance": "Formatting & Layout Standards",
    "Readability & Active Verbs": "Bullet Point Quality & Verbs",
}

if ats_report.components:
    d_rows = []
    for comp_key, comp in ats_report.components.items():
        friendly_comp = COMP_FRIENDLY_NAMES.get(comp.name, comp.name)
        d_rows.append({
            "Evaluation Component": friendly_comp,
            "Score": f"{comp.score:.1f}%",
            "Weight": f"{comp.weight * 100:.0f}%",
            "Weighted Score": f"{comp.weighted_score:.1f}",
            "Explanation": comp.explanation,
        })
    st.dataframe(pd.DataFrame(d_rows), use_container_width=True, hide_index=True)

st.markdown("---")

# 5. Requirements Matching Tabs
tab_matched, tab_missing, tab_risks, tab_opt = st.tabs([
    "📋 Requirements Coverage Matrix",
    "❌ Missing Important Keywords",
    "🚨 Formatting & Layout Checks",
    "💡 Optimization Suggestions",
])

with tab_matched:
    st.markdown("### Job Requirements Coverage Matrix")
    if ats_report.coverage_matrix:
        cov_rows = []
        for r in ats_report.coverage_matrix:
            cov_rows.append({
                "Requirement": r.requirement,
                "Importance": r.importance.value if hasattr(r.importance, "value") else str(r.importance),
                "Match Level": r.match_level.value if hasattr(r.match_level, "value") else str(r.match_level),
                "Resume Evidence": r.resume_evidence or "None",
                "Truth Status": r.truth_status,
                "Recommendation": r.recommendation,
            })
        st.dataframe(pd.DataFrame(cov_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No coverage items found.")

with tab_missing:
    st.markdown("### Missing / Unaddressed Requirements")
    if ats_report.missing_requirements:
        for r in ats_report.missing_requirements:
            st.error(f"❌ **{r.requirement}** ({r.importance.value if hasattr(r.importance, 'value') else str(r.importance)}) — {r.explanation}\n\n*Action: {r.recommendation}*")
    else:
        st.success("All core requirements are addressed!")

with tab_risks:
    st.markdown("### ATS Format & Parsing Traps")
    c_fmt, c_stf = st.columns(2)
    with c_fmt:
        st.markdown("**Formatting Integrity:**")
        if ats_report.formatting_risks:
            for fr in ats_report.formatting_risks:
                st.warning(f"⚠ **{fr.description}** ({fr.severity.value if hasattr(fr.severity, 'value') else str(fr.severity)}) — {fr.recommendation}")
        else:
            st.success("✓ Single-column standard layout verified")
            st.success("✓ Zero hidden tables or text boxes")
            st.success("✓ Standard web-safe font hierarchy")
    with c_stf:
        st.markdown("**Keyword Findings & Natural Repetition:**")
        if ats_report.keyword_density_findings:
            for w in ats_report.keyword_density_findings:
                st.info(f"ℹ️ {w}")
        else:
            st.success("✓ Keyword repetition within safe natural density limits (<3.5%).")

with tab_opt:
    st.markdown("### Resume Optimization Suggestions")
    if ats_report.suggestions:
        for idx, sug in enumerate(ats_report.suggestions, 1):
            prio = sug.priority.value if hasattr(sug.priority, "value") else str(sug.priority)
            st.info(f"**[{prio}] {sug.category}:** {sug.recommended_action}\n\n*Reason: {sug.reason}*")
    else:
        st.success("Resume is already optimally formatted for ATS screening!")
        
    st.markdown("---")
    st.markdown("#### 🔄 Explicit Action")
    if st.button("✨ Regenerate Tailored Resume with Alternative Strategy", type="primary"):
        st.info("Navigate to **Resume Builder** to choose an explicit strategy override and re-tailor.")
