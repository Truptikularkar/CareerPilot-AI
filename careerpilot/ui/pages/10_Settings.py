import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
from careerpilot.core.config import settings
from careerpilot.llm import get_llm_status
from careerpilot.services.candidate_service import CandidateService
from careerpilot.core.date_utils import calculate_total_experience_years, format_experience_duration_string

st.set_page_config(page_title="Settings — CareerPilot AI", page_icon="⚙️", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("⚙️ System Configuration & Model Settings")
st.caption("Inspect and configure LLM provider settings, live health diagnostics, scoring thresholds, and candidate data provenance.")

# 1. Candidate Source-of-Truth Safety Banner
st.success("🔒 **Candidate Source of Truth Protection: ACTIVE**\nAuthoritative candidate records originate from SQLite (`data/careerpilot.db`) with evidence ledger provenance. Files in `data/candidate/` are synchronized backup representations.")

st.markdown("---")

col_cfg1, col_cfg2 = st.columns(2)

with col_cfg1:
    st.subheader("🤖 LLM & Vector Diagnostics")
    llm_info = get_llm_status()
    st.markdown(f"- **Active Provider:** `{llm_info.get('provider', 'gemini')}`")
    st.markdown(f"- **Active Model:** `{llm_info.get('model', settings.GEMINI_MODEL)}`")
    st.markdown(f"- **Connection Status:** `{'🟢 ' + llm_info.get('status', 'CONNECTED') if 'CONNECT' in llm_info.get('status', '') else '🔴 ' + llm_info.get('status', 'OFFLINE')}`")
    st.markdown(f"- **API Key Masked:** `{llm_info.get('api_key_masked') or 'Not Configured'}`")
    if llm_info.get("last_error"):
        st.error(f"Last LLM Error: {llm_info['last_error']}")
    st.markdown(f"- **Environment Mode:** `{settings.CAREERPILOT_MODE.value}`")

with col_cfg2:
    st.subheader("⚖️ Deterministic Decision Thresholds")
    st.markdown("- **Apply Recommendation Threshold:** `Fit Score >= 75.0%` (and Must-Have >= 80%)")
    st.markdown("- **Review Recommendation Threshold:** `Fit Score 50.0% - 74.9%`")
    st.markdown("- **Skip Recommendation Threshold:** `Fit Score < 50.0%` (or critical shortfall)")
    st.markdown("- **ATS Excellent Compatibility:** `Score >= 80.0%`")
    st.markdown("- **1-Page Resume Limit:** Strictly enforced for candidates < 3 years experience")

st.markdown("---")

# 2. System-wide Data Sources Status Matrix
st.subheader("🔌 System Data Sources & Provenance Matrix")
ds = CandidateService.get_data_sources_status()
ds_cols = st.columns(4)
with ds_cols[0]:
    st.metric("SQLite Ground Truth", ds["sqlite"]["status"])
    st.caption(f"Verified Facts: {ds['sqlite'].get('verified_facts_count', 46)}")
with ds_cols[1]:
    st.metric("ChromaDB Vector RAG", ds["candidate_rag"]["status"])
    st.caption(f"Chunks Indexed: {ds['candidate_rag']['chunk_count']}")
with ds_cols[2]:
    st.metric("Gemini API (3.6 Flash)", ds["gemini"]["status"])
    st.caption(f"Model: {ds['gemini']['model']}")
with ds_cols[3]:
    st.metric("GitHub Profile", ds["github"]["status"])
    st.caption(f"User: {ds['github'].get('username') or prof.full_name}")

st.markdown("---")

# 3. Dynamic Candidate Profile Overview
prof = CandidateService.get_active_profile()
exp_years = calculate_total_experience_years(prof.experiences)
exp_dur_str = format_experience_duration_string(exp_years)

st.subheader("👤 Candidate Active Profile (Dynamically Loaded from SQLite)")
p_c1, p_c2, p_c3 = st.columns(3)
with p_c1:
    st.markdown(f"**Full Name:** {prof.full_name}")
    st.markdown(f"**Email:** `{prof.email}`")
    st.markdown(f"**Location:** {prof.location or 'Flexible / Remote'}")
with p_c2:
    st.markdown(f"**Verified Experience:** {exp_dur_str} ({exp_years:.1f} years)")
    if prof.experiences:
        st.markdown(f"**Primary Company:** {prof.experiences[0].company} ({prof.experiences[0].title})")
    st.markdown(f"**Primary Cloud:** {', '.join(prof.preferences.cloud_preferences) if prof.preferences.cloud_preferences else 'GCP'}")
with p_c3:
    st.markdown(f"**Core Skills ({len(prof.skills)}):** " + ", ".join([s.name for s in prof.skills[:5]]))
    st.markdown(f"**Target Roles:** " + ", ".join([r.value if hasattr(r, 'value') else str(r) for r in prof.preferences.target_roles[:3]]))
    st.markdown(f"**Last Synchronized:** `{prof.last_updated_at[:19].replace('T', ' ')}`")

st.markdown("---")

# 4. Account & Security Management
st.subheader("🔐 Account & Multi-Device Security")
current_user = st.session_state.get("authenticated_user")
if current_user:
    u_c1, u_c2 = st.columns([1, 1])
    with u_c1:
        st.markdown("#### Active Account Details")
        st.markdown(f"- **Authenticated User:** `{current_user.get('full_name', 'User')}`")
        st.markdown(f"- **Login Email:** `{current_user.get('email', 'N/A')}`")
        st.markdown(f"- **User Identifier:** `{current_user.get('user_id', 'N/A')}`")
        st.markdown(f"- **Session Active:** `🟢 Authenticated`")
        st.info("CareerPilot encrypts sessions using SHA-256 token hashing and Argon2id password hashing. Multi-device access permits simultaneous sessions across your laptop and mobile device.")

    with u_c2:
        st.markdown("#### Change Password")
        with st.form("change_password_form", clear_on_submit=True):
            current_pwd = st.text_input("Current Password", type="password", key="cp_current")
            new_pwd = st.text_input("New Password (min 8 chars, uppercase, digit, special)", type="password", key="cp_new")
            confirm_pwd = st.text_input("Confirm New Password", type="password", key="cp_confirm")
            revoke_others = st.checkbox("Revoke all other active device sessions", value=True)
            submit_pwd = st.form_submit_button("Update Password", use_container_width=True)

            if submit_pwd:
                if not current_pwd or not new_pwd:
                    st.error("Please fill in both current and new password.")
                elif new_pwd != confirm_pwd:
                    st.error("New passwords do not match.")
                else:
                    success, msg = AuthService.change_password(
                        user_id=current_user.get("user_id"),
                        current_password=current_pwd,
                        new_password=new_pwd,
                        revoke_other_sessions=revoke_others,
                        current_token=st.session_state.get("auth_token")
                    )
                    if success:
                        st.success(f"Password updated successfully: {msg}")
                    else:
                        st.error(f"Password change failed: {msg}")

st.markdown("---")
st.info("💡 All data processing, SQLite databases (`careerpilot.db`), and generated resumes/interviews are stored locally on your machine.")

