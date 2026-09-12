import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import pandas as pd
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.db.repository import JobRepository, MockSessionRepository, AnalyticsRepository
from careerpilot.core.constants import ApplicationStatus, DecisionRecommendation

st.set_page_config(page_title="Dashboard — CareerPilot AI", page_icon="📊", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("📊 Candidate Career Intelligence Dashboard")
st.caption("High-level overview of job opportunities, applications, interview preparation, and readiness.")

metrics = CareerPilotService.get_dashboard_metrics()

# 1. KPI Metric Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Jobs Analyzed", metrics.total_jobs_analyzed)
    st.metric("Jobs to Apply", metrics.jobs_to_apply)
with c2:
    st.metric("Jobs in Review", metrics.jobs_reviewed)
    st.metric("Jobs Skipped", metrics.jobs_skipped)
with c3:
    st.metric("Applications Active", metrics.applications_submitted)
    st.metric("Interview Preps", metrics.interview_preps_completed)
with c4:
    st.metric("Mock Interviews", metrics.mock_interviews_completed)
    st.metric("Avg Mock Score", f"{metrics.average_mock_score}%" if metrics.average_mock_score else "N/A")

st.markdown("---")

# 2. Career Intelligence & Funnel Analytics
st.subheader("🚀 Career Intelligence & Pipeline Insights")
insights = AnalyticsRepository.get_career_insights()
ci1, ci2, ci3, ci4 = st.columns(4)
with ci1:
    st.metric("Interview Conversion Rate", insights.get("interview_conversion_rate", "0.0%"))
with ci2:
    st.metric("Applications Submitted", insights.get("applications_sent", 0))
with ci3:
    st.metric("Interviews Secured", insights.get("interviews_secured", 0))
with ci4:
    st.metric("Average Job Fit Score", f"{insights.get('average_fit_score', 0.0):.1f}%")

if insights.get("most_applied_roles"):
    st.markdown(f"**Top Target Roles in Market:** " + " • ".join([f"`{r}`" for r in insights["most_applied_roles"][:3]]))

st.markdown("---")

# 3. Active Applications & Next Action System
st.subheader("📋 Active Applications & Next Recommended Actions")
apps = CareerPilotService.list_applications()

if apps:
    from careerpilot.core.terminology import get_friendly_status_label, get_friendly_decision_label
    app_data = []
    for a in apps[:10]:
        app_data.append({
            "Company": a.company,
            "Role": a.job_title,
            "Location": a.job_location,
            "Fit Score": f"{a.fit_score:.1f}%",
            "ATS Score": f"{a.ats_score:.1f}%" if a.ats_score else "Pending",
            "Recommendation": get_friendly_decision_label(a.system_recommendation),
            "Decision": get_friendly_decision_label(a.user_decision),
            "Status": get_friendly_status_label(a.application_status),
            "Next Action": a.next_action or "Review requirements",
        })
    df_apps = pd.DataFrame(app_data)
    st.dataframe(df_apps, use_container_width=True, hide_index=True)
else:
    st.info("No applications tracked yet. Use **Analyze Job** to add your first job description.")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

from careerpilot.ui.utils.formatters import format_date, format_datetime

with col_left:
    st.subheader("💼 Recent Analyzed Jobs")
    jobs = JobRepository.list_jobs()
    if jobs:
        job_data = []
        for j in jobs[:6]:
            job_data.append({
                "Company": j.company_name or "N/A",
                "Job Title": j.job_title or "N/A",
                "Role Category": j.extracted_role,
                "Seniority": j.estimated_seniority,
                "Date": format_date(j.created_at),
            })
        st.dataframe(pd.DataFrame(job_data), use_container_width=True, hide_index=True)
    else:
        st.write("No jobs parsed yet.")

with col_right:
    st.subheader("🎯 Preparation Weaknesses & Study Focus")
    skill_summary = CareerPilotService.get_skill_gaps_summary()
    if skill_summary.priority_learning_topics:
        for idx, topic in enumerate(skill_summary.priority_learning_topics[:4], 1):
            st.warning(f"**{idx}.** {topic}")
    else:
        st.success("No critical skill weaknesses detected! Candidate is ready for technical screening.")

    st.markdown("---")
    st.subheader("🎙️ Recent Mock Interview Sessions")
    mock_sessions = MockSessionRepository.list_all_sessions()
    if mock_sessions:
        m_data = []
        for m in mock_sessions[:5]:
            final_rep = (m.readiness_json or {}).get("final_report", {})
            score = final_rep.get("overall_score", "In Progress")
            score_str = f"{score}%" if isinstance(score, (int, float)) else str(score)
            m_data.append({
                "Session ID": m.id,
                "Target Role": m.target_role,
                "Difficulty": m.current_difficulty,
                "Turns": len(m.turns_json or []),
                "Score": score_str,
                "Status": "Completed" if m.is_completed else "Active",
                "Date": format_datetime(m.created_at),
            })
        st.dataframe(pd.DataFrame(m_data), use_container_width=True, hide_index=True)
    else:
        st.write("No mock interview sessions recorded yet. Practice in **Mock Interview**.")

