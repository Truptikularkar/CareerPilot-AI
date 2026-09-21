import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
from careerpilot.core.config import settings
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import ApplicationStatus, AppEnvironmentMode
from careerpilot.health import get_system_health
from careerpilot.rag.indexer import build_or_load_indexes

st.set_page_config(
    page_title="CareerPilot AI — Personal Job Intelligence & Career Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Startup Vector Store & DB Check (Cached across reruns)
@st.cache_resource
def initialize_system():
    from careerpilot.db.session import init_db
    init_db()
    return build_or_load_indexes(force_reindex=False)

initialize_system()

# Authentication Gatekeeper
from careerpilot.services.auth_service import AuthService
from careerpilot.ui.auth_view import render_login_page

auth_user = st.session_state.get("authenticated_user")
token = st.session_state.get("auth_session_token")
if not auth_user and token:
    auth_user = AuthService.validate_session(token)
    if auth_user:
        st.session_state["authenticated_user"] = auth_user
        st.session_state["authenticated_candidate_id"] = auth_user.candidate_id

if not auth_user:
    render_login_page()
    st.stop()

# Custom CSS for professional clean UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-apply {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-review {
        background-color: #FEF9C3;
        color: #854D0E;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-skip {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Branding & Candidate Status
with st.sidebar:
    st.title("🚀 CareerPilot AI")
    st.caption("Personal Job Intelligence & Interview Agent")
    st.markdown("---")

    if auth_user:
        st.markdown(f"👤 **User:** {auth_user.full_name}")
        st.caption(f"📧 `{auth_user.email}`")
        if st.button("🚪 Sign Out", key="app_logout_btn", use_container_width=True):
            if token:
                AuthService.logout(token)
            st.session_state.clear()
            st.rerun()
        st.markdown("---")
    
    from careerpilot.services.candidate_service import CandidateService
    from careerpilot.llm import get_llm_status
    active_cand = CandidateService.get_active_profile()

    if active_cand.id == "trupti_kularkar":
        st.info("🌐 **Environment:** SAMPLE PORTFOLIO BASELINE\n\n*Verified Candidate Profile Active.*")
        st.markdown("### 👤 Candidate Profile")
        st.markdown(f"**{active_cand.full_name}**")
        st.markdown(f"📍 {active_cand.location or 'Pune, Maharashtra, India'}")
        if active_cand.experiences:
            exp0 = active_cand.experiences[0]
            st.markdown(f"💼 **{exp0.title}** at {exp0.company}")
        st.success("🔒 Candidate Ground-Truth: **Verified Portfolio Baseline**")
    else:
        st.success("🔒 **Environment:** PERSONAL CANDIDATE ACCOUNT\n\n*Canonical SQLite / PostgreSQL Ground Truth.*")
        st.markdown("### 👤 Candidate Profile")
        st.markdown(f"**{active_cand.full_name}**")
        st.markdown(f"📍 {active_cand.location or 'Flexible / Remote'}")
        if active_cand.experiences:
            exp0 = active_cand.experiences[0]
            st.markdown(f"💼 **{exp0.title}** at {exp0.company}")
        contact_parts = []
        if active_cand.email:
            contact_parts.append(f"📧 {active_cand.email}")
        if active_cand.phone:
            contact_parts.append(f"📞 {active_cand.phone}")
        if contact_parts:
            st.caption(" | ".join(contact_parts))
        st.success("🔒 Candidate Ground-Truth: **Personal Verified Ledger**")

    st.markdown("---")
    st.markdown("### 🔌 Live Data Sources")
    ds = CandidateService.get_data_sources_status()
    st.markdown(f"- 🗄️ SQLite Truth: **{ds['sqlite']['status']}**")
    st.markdown(f"- 🧠 ChromaDB RAG: **{ds['candidate_rag']['status']}** ({ds['candidate_rag']['chunk_count']} chunks)")
    st.markdown(f"- ⚡ Gemini API: **{ds['gemini']['status']}** (`{ds['gemini']['model']}`)")
    st.markdown(f"- 🐙 GitHub: **{ds['github']['status']}**")
    st.markdown(f"- 💼 LinkedIn: **{ds['linkedin']['status'][:14]}...**")
        
    st.markdown("---")
    
    metrics = CareerPilotService.get_dashboard_metrics()
    st.markdown("### 📊 Quick Stats")
    st.markdown(f"- Analyzed Jobs: **{metrics.total_jobs_analyzed}**")
    st.markdown(f"- Recommended Apply: **{metrics.jobs_to_apply}**")
    st.markdown(f"- Applications Active: **{metrics.applications_submitted}**")
    st.markdown(f"- Mock Interviews: **{metrics.mock_interviews_completed}**")
    st.markdown("---")
    st.caption("CareerPilot AI v1.0 • Local Ground Truth • Zero-Fabrication")

# Main Welcome View
st.markdown('<div class="main-header">Welcome to CareerPilot AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your autonomous, evidence-grounded career intelligence, resume tailoring, and interview preparation copilot.</div>', unsafe_allow_html=True)

if active_cand.id == "trupti_kularkar":
    st.info(f"ℹ️ **Sample Profile Active:** Operating with verified candidate baseline (**{active_cand.full_name}**). Evidence and AI models active.")
else:
    st.info(f"ℹ️ **Personal Profile Active:** Operating with your candidate profile (**{active_cand.full_name}**). Use **Candidate Profile** in the left sidebar to update skills, add projects, or import a resume.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Jobs Analyzed", metrics.total_jobs_analyzed)
with col2:
    st.metric("Jobs to Apply", metrics.jobs_to_apply)
with col3:
    st.metric("Applications Active", metrics.applications_submitted)
with col4:
    st.metric("Avg Mock Score", f"{metrics.average_mock_score}%" if metrics.average_mock_score else "N/A")

st.markdown("---")

# Health Check Expander
with st.expander("🩺 System Diagnostics & Health Status", expanded=False):
    health = get_system_health()
    if health.overall_status.value == "HEALTHY":
        st.success(f"System Status: **{health.overall_status.value}** — All sub-systems operational.")
    elif health.overall_status.value == "DEGRADED":
        st.warning(f"System Status: **{health.overall_status.value}** — System running with fallback mechanisms.")
    else:
        st.error(f"System Status: **{health.overall_status.value}** — One or more core dependencies are unavailable.")

    h_cols = st.columns(3)
    for idx, comp in enumerate(health.components):
        with h_cols[idx % 3]:
            badge = "🟢" if comp.status.value == "HEALTHY" else ("🟡" if comp.status.value == "DEGRADED" else "🔴")
            st.markdown(f"**{badge} {comp.name}**")
            st.caption(comp.message)

st.markdown("---")

st.markdown("### 🧭 Unified Workflow Navigation")
st.markdown("""
Use the sidebar pages to navigate through the end-to-end career workflow:

1. **📊 Dashboard** (`1_Dashboard.py`): Overview of applications, mock interview scores, and preparation gaps.
2. **🔍 Analyze Job** (`2_Analyze_Job.py`): Paste or upload any job description to evaluate real role classification, candidate fit score, and get deterministic **APPLY / REVIEW / SKIP** recommendations.
3. **📋 Applications** (`3_Applications.py`): Manage your job application pipeline, version history, and next recommended actions.
4. **📄 Resume Builder** (`4_Resume_Builder.py`): Generate evidence-grounded, truth-audited tailored resumes with ATS-friendly DOCX and PDF export.
5. **🎯 ATS Analysis** (`5_ATS_Analysis.py`): Inspect keyword coverage, formatting safety, and deterministic ATS-style compatibility scores.
6. **📚 Interview Prep** (`6_Interview_Prep.py`): Access role-specific technical Q&A, STAR behavioral stories, system design architectures, and multi-day study roadmaps.
7. **🎙️ Mock Interview** (`7_Mock_Interview.py`): Practice real-time, 10-dimensional adaptive mock interviews with live coaching feedback.
8. **📈 Skill Gaps** (`8_Skill_Gaps.py`): Discover aggregated market skill demand and transferable learning priorities.
9. **👤 Candidate Profile** (`9_Candidate_Profile.py`): Manage master candidate profile, add projects/skills, career preferences, master resume diff review, version history, and RAG sync.
10. **⚙️ Settings** (`10_Settings.py`): View system configuration and candidate profile verification status.
11. **ℹ️ About** (`11_About.py`): Architecture, technology stack, and portfolio overview.
12. **🧪 Evaluation** (`12_Evaluation.py`): Deep multi-dataset AI evaluation and RAG observability benchmarks.

""")

st.info("💡 **Getting Started:** Navigate to **Analyze Job** in the left sidebar to parse your first job description and evaluate candidate fit.")
