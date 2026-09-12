import streamlit as st
import pandas as pd
from careerpilot.services.careerpilot_service import CareerPilotService

st.set_page_config(page_title="Skill Gaps — CareerPilot AI", page_icon="📈", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("📈 Aggregated Skill Demand & Market Intelligence")
st.caption("Cross-application intelligence identifying market skill demand, candidate verified strengths, transferable experience, and priority learning topics.")

skill_summary = CareerPilotService.get_skill_gaps_summary()

# 1. Summary Cards
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Top Missing Skills", len(skill_summary.top_missing_skills))
with c2:
    st.metric("Top Demanded Skills", len(skill_summary.top_demanded_skills))
with c3:
    st.metric("Priority Learning Actions", len(skill_summary.priority_learning_topics))

st.markdown("---")

# 2. Priority Learning Topics
st.subheader("🎯 Prioritized Learning Roadmap (Ranked by Frequency & Role Relevance)")
st.info("💡 **Guiding Principle:** CareerPilot does NOT treat every missing skill as a learning requirement. Only high-frequency requirements for target roles (e.g. AI Data Engineer) are recommended for focused preparation.")

for idx, topic in enumerate(skill_summary.priority_learning_topics, 1):
    st.warning(f"**{idx}.** {topic}")

st.markdown("---")

col_missing, col_demanded = st.columns(2)

with col_missing:
    st.subheader("⚠️ Most Requested Missing Skills Across Analyzed JDs")
    if skill_summary.top_missing_skills:
        m_rows = []
        for item in skill_summary.top_missing_skills:
            m_rows.append({
                "Skill Name": item.skill_name,
                "JD Frequency": f"{item.frequency_count} Jobs",
                "Candidate Status": item.candidate_status,
                "Preparation Action": item.recommendation,
            })
        st.dataframe(pd.DataFrame(m_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No missing skill trends yet. Analyze more jobs in **Analyze Job**.")

with col_demanded:
    st.subheader("💪 Most Demanded Technologies & Candidate Alignment")
    if skill_summary.top_demanded_skills:
        d_rows = []
        for item in skill_summary.top_demanded_skills:
            d_rows.append({
                "Skill Name": item.skill_name,
                "JD Frequency": f"{item.frequency_count} Jobs",
                "Candidate Status": item.candidate_status,
                "Status Type": item.recommendation,
            })
        st.dataframe(pd.DataFrame(d_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No demand trends yet.")

st.markdown("---")
from careerpilot.services.candidate_service import CandidateService
from careerpilot.core.date_utils import calculate_total_experience_years, format_experience_duration_string
_prof = CandidateService.get_active_profile()
_years = calculate_total_experience_years(_prof.experiences)
_cloud_str = ", ".join(_prof.preferences.cloud_preferences) if _prof.preferences.cloud_preferences else "GCP"
st.caption(f"Candidate Profile: {_prof.full_name} | {format_experience_duration_string(_years)} | Target Cloud: {_cloud_str}")
