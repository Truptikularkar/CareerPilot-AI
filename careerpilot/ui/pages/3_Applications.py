import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import pandas as pd
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import ApplicationStatus, DecisionRecommendation
from careerpilot.db.repository import JobRepository, ResumeRepository, MockSessionRepository, InterviewPrepRepository
from careerpilot.ui.utils.formatters import format_datetime


st.set_page_config(page_title="Applications — CareerPilot AI", page_icon="📋", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("📋 Job Applications & Pipeline Tracker")
st.caption("Track, inspect, and manage your tailored applications, resume versions, notes, and preparation history.")

# 1. Filters & Search Bar
f_col1, f_col2, f_col3, f_col4 = st.columns(4)

with f_col1:
    status_filter = st.selectbox(
        "Filter by Status:",
        ["All"] + [s.value for s in ApplicationStatus],
    )
with f_col2:
    rec_filter = st.selectbox(
        "Filter by Recommendation:",
        ["All"] + [r.value for r in DecisionRecommendation],
    )
with f_col3:
    role_filter = st.text_input("Filter by Role:", placeholder="e.g. Data Engineer")
with f_col4:
    search_filter = st.text_input("Search Company / Keywords:", placeholder="e.g. Acme")

# Fetch applications
all_apps = CareerPilotService.list_applications()

# Apply local filtering
filtered_apps = all_apps
if status_filter != "All":
    filtered_apps = [a for a in filtered_apps if a.application_status.value == status_filter]
if rec_filter != "All":
    filtered_apps = [a for a in filtered_apps if a.system_recommendation.value == rec_filter or a.user_decision.value == rec_filter]
if role_filter:
    filtered_apps = [a for a in filtered_apps if role_filter.lower() in a.job_title.lower()]
if search_filter:
    filtered_apps = [a for a in filtered_apps if search_filter.lower() in a.company.lower() or search_filter.lower() in a.job_title.lower()]

st.markdown(f"**Found {len(filtered_apps)} matching applications**")

# 2. Main Applications Table
if filtered_apps:
    from careerpilot.core.terminology import get_friendly_status_label, get_friendly_decision_label
    table_rows = []
    for a in filtered_apps:
        table_rows.append({
            "App ID": a.application_id,
            "Company": a.company,
            "Job Title": a.job_title,
            "Location": a.job_location,
            "Fit Score": f"{a.fit_score:.1f}%",
            "ATS Score": f"{a.ats_score:.1f}%" if a.ats_score is not None else "Pending",
            "Recommendation": get_friendly_decision_label(a.system_recommendation),
            "Decision": get_friendly_decision_label(a.user_decision),
            "Status": get_friendly_status_label(a.application_status),
            "Next Action": a.next_action or "Review application",
        })
    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No applications found matching the filter criteria.")

st.markdown("---")

# 3. Application Deep Inspector
st.subheader("🔍 Application Deep Inspector")

app_options = {f"{a.company} — {a.job_title} ({a.application_id})": a for a in all_apps}
if app_options:
    selected_label = st.selectbox("Select an Application to inspect details:", list(app_options.keys()))
    selected_app = app_options[selected_label]
    
    st.markdown(f"### **{selected_app.company}** — {selected_app.job_title}")
    st.markdown(f"📍 `{selected_app.job_location}` | 🆔 App ID: `{selected_app.application_id}` | 💼 Job ID: `{selected_app.job_id}`")
    
    # Detail tabs
    tab_summary, tab_resumes, tab_notes, tab_prep, tab_status = st.tabs([
        "📊 Job Summary & Fit",
        "📄 Resume Versions & ATS",
        "📝 Notes & Activity",
        "🎙️ Preparation & Mocks",
        "⚙️ Update Status & Decision",
    ])
    
    with tab_summary:
        s_c1, s_c2, s_c3 = st.columns(3)
        with s_c1:
            st.metric("Candidate Fit Score", f"{selected_app.fit_score:.1f}%")
        with s_c2:
            st.metric("System Recommendation", get_friendly_decision_label(selected_app.system_recommendation))
        with s_c3:
            st.metric("Current Status", get_friendly_status_label(selected_app.application_status))
            
        st.markdown(f"**Suggested Next Action:** `{selected_app.next_action}`")
        if selected_app.job_description:
            with st.expander("View Full Job Description Text"):
                st.text(selected_app.job_description)

    with tab_resumes:
        st.markdown("#### 📄 Resume Version History")
        if selected_app.resume_versions:
            v_data = []
            for v in selected_app.resume_versions:
                v_data.append({
                    "Version": v.version_tag,
                    "Strategy": v.strategy_type,
                    "ATS Score": f"{v.ats_score:.1f}%" if v.ats_score else "N/A",
                    "DOCX Available": "✅ Yes" if v.docx_file_path else "❌ No",
                    "PDF Available": "✅ Yes" if v.pdf_file_path else "❌ No",
                    "Created At": format_datetime(v.created_at),

                })
            st.dataframe(pd.DataFrame(v_data), use_container_width=True, hide_index=True)
            
            # Download latest files
            latest_v = selected_app.resume_versions[-1]
            cd1, cd2 = st.columns(2)
            with cd1:
                if latest_v.docx_file_path and Path(latest_v.docx_file_path).exists():
                    with open(latest_v.docx_file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {latest_v.version_tag} DOCX",
                            data=f.read(),
                            file_name=f"{selected_app.company.replace(' ', '_')}_Resume_{latest_v.version_tag}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
            with cd2:
                if latest_v.pdf_file_path and Path(latest_v.pdf_file_path).exists():
                    with open(latest_v.pdf_file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {latest_v.version_tag} PDF",
                            data=f.read(),
                            file_name=f"{selected_app.company.replace(' ', '_')}_Resume_{latest_v.version_tag}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

        else:
            st.info("No tailored resume generated yet. Use **Resume Builder** to generate version v1.0.")

    with tab_notes:
        st.markdown("#### 📝 Candidate Notes & Logged Activity")
        if selected_app.notes:
            for n in selected_app.notes:
                st.markdown(f"- {n}")
        else:
            st.write("No notes recorded for this application.")
            
        new_note_text = st.text_input("Add a Note (e.g., 'Recruiter reached out on LinkedIn', 'Referral applied'):", key="add_note_input")
        if st.button("➕ Add Note", key="add_note_btn"):
            if new_note_text.strip():
                updated = CareerPilotService.add_application_note(selected_app.application_id, new_note_text.strip())
                st.success("Note added successfully!")
                st.rerun()

    with tab_prep:
        st.markdown("#### 🎙️ Interview Preparation & Mock Sessions")
        prep_db = InterviewPrepRepository.get_prep_for_job(selected_app.job_id)
        if prep_db:
            st.success(f"✅ Interview Preparation Plan Generated! (Readiness Score: **{prep_db.readiness_score:.1f}%**)")
        else:
            st.info("No interview preparation plan generated yet. Generate one in **Interview Prep**.")
            
        sessions = MockSessionRepository.list_sessions_for_job(selected_app.job_id)
        if sessions:
            st.markdown(f"**Completed / Active Mock Sessions ({len(sessions)}):**")
            for s in sessions:
                final_rep = (s.readiness_json or {}).get("final_report", {})
                score = final_rep.get("overall_score", "In Progress")
                st.markdown(f"- **Session `{s.id}`** | Difficulty: `{s.current_difficulty}` | Score: `{score}%`")
        else:
            st.write("No mock interview practice sessions recorded for this role yet.")

    with tab_status:
        st.markdown("#### ⚙️ Application Pipeline Status & Provenance")
        from careerpilot.db.repository import ApplicationRepository
        
        meta_c1, meta_c2, meta_c3 = st.columns(3)
        with meta_c1:
            st.markdown(f"**Canonical Job ID:** `{getattr(selected_app, 'canonical_job_id', 'cjob_auto')}`")
        with meta_c2:
            st.markdown(f"**Application Source:** `{getattr(selected_app, 'source', 'DIRECT')}`")
        with meta_c3:
            st.markdown(f"**Recruiter:** `{getattr(selected_app, 'recruiter', 'Pending Assignment')}`")

        st.markdown("---")
        st.markdown("##### Change Status")
        st_c1, st_c2 = st.columns(2)
        with st_c1:
            curr_val = selected_app.application_status.value
            status_list = [s.value for s in ApplicationStatus]
            default_idx = status_list.index(curr_val) if curr_val in status_list else 0
            new_status_str = st.selectbox(
                "Pipeline Status (17 Lifecycle Stages):",
                status_list,
                format_func=lambda s: get_friendly_status_label(s),
                index=default_idx,
            )
        with st_c2:
            status_note = st.text_input("Status Transition Note:", placeholder="e.g. Cleared technical screening, scheduled technical interview")
            
        if st.button("💾 Update Pipeline Status", type="primary"):
            CareerPilotService.update_application_status(
                selected_app.application_id,
                ApplicationStatus(new_status_str),
                notes=status_note if status_note else None,
            )
            st.success(f"Pipeline status updated to: **{get_friendly_status_label(new_status_str)}**")
            st.rerun()

        st.markdown("---")
        st.markdown("##### 📜 Status Transition History")
        history = ApplicationRepository.get_status_history(selected_app.application_id)
        if history:
            h_rows = []
            for h in reversed(history):
                h_rows.append({
                    "Timestamp": h.get("timestamp", "")[:19].replace("T", " "),
                    "From Status": h.get("from_status", "N/A"),
                    "To Status": h.get("to_status", "N/A"),
                    "Note / Details": h.get("note", ""),
                })
            st.dataframe(pd.DataFrame(h_rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No historical transitions recorded yet for this application.")
else:
    st.info("No applications to inspect yet.")
