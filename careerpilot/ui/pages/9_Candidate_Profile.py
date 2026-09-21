import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from careerpilot.services.candidate_service import CandidateService
from careerpilot.services.resume_import_service import ResumeImportService
from careerpilot.models.candidate import (
    CandidateProfile,
    Skill,
    Experience,
    Project,
    Education,
    Achievement,
    CareerPreference,
    ProfileDiffItem,
)
from careerpilot.core.constants import SkillCategory, RoleCategory, SeniorityLevel
from careerpilot.ui.utils.formatters import format_datetime
from careerpilot.core.date_utils import calculate_total_experience_years, format_experience_duration_string

st.set_page_config(page_title="Candidate Profile — CareerPilot AI", page_icon="👤", layout="wide")

from careerpilot.services.auth_service import AuthService

AuthService.require_auth()


st.title("👤 Candidate Profile Manager")
st.caption("Manage your authoritative candidate facts, professional experience, projects, verified skills, and Candidate RAG synchronization.")

# 1. Fetch Active Profile & Health Summary
try:
    profile = CandidateService.get_active_profile()
    health = CandidateService.get_profile_health(profile)
    rag_status = CandidateService.get_rag_sync_status()
    total_exp_years = calculate_total_experience_years(profile.experiences)
    exp_str = format_experience_duration_string(total_exp_years)
except Exception as e:
    logger.exception("Error loading candidate profile: %s", e)
    st.error("We couldn't load your candidate profile. Please refresh the page. If the problem continues, check your Candidate Profile settings.")
    st.stop()

# 2. Top Metric Bar & Profile Health
col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns(5)
with col_h1:
    st.metric("Profile Completeness", f"{health.completeness_score:.0f}%")
with col_h2:
    st.metric("Total Experience", exp_str)
with col_h3:
    st.metric("Evidence Status", rag_status["status_label"])
with col_h4:
    st.metric("Evidence Items", rag_status["chunk_count"])
with col_h5:
    if st.button("🔄 Re-sync Evidence", use_container_width=True, help="Update search index from latest profile evidence"):
        with st.spinner("Syncing Candidate Evidence..."):
            total_indexed = CandidateService.rebuild_candidate_rag()
            st.success(f"Candidate evidence synced ({total_indexed} items)!")
            st.rerun()

st.caption(f"**Last Profile Update:** `{format_datetime(profile.last_updated_at)}` | **Last Sync:** `{format_datetime(rag_status['last_rag_sync'])}`")

st.markdown("---")

# 3. Main Navigation Tabs
tab_overview, tab_exp, tab_projects, tab_skills, tab_edu, tab_certs_achieve, tab_pref, tab_external, tab_import, tab_history = st.tabs([
    "👤 Personal Information",
    "💼 Experience",
    "🚀 Projects",
    "🛠️ Skills",
    "🎓 Education",
    "🏆 Certifications",
    "🎯 Preferences",
    "🌐 External Profiles",
    "📥 Evidence",
    "🕒 Version History",
])

# -----------------------------------------------------------------------------
# TAB 1: Overview
# -----------------------------------------------------------------------------
with tab_overview:
    st.subheader("Candidate Master Contact & Summary")
    st.info("💡 Candidate facts entered here are authoritative and will be preserved verbatim during resume generation.")

    with st.form("profile_overview_form"):
        o_c1, o_c2 = st.columns(2)
        with o_c1:
            full_name = st.text_input("Full Name*:", value=profile.full_name)
            email = st.text_input("Email Address:", value=profile.email or "")
            phone = st.text_input("Phone Number:", value=profile.phone or "")
            location = st.text_input("Current Location:", value=profile.location or "", placeholder="e.g. Pune, Maharashtra, India or Remote")
        with o_c2:

            linkedin_url = st.text_input("LinkedIn Profile URL:", value=profile.linkedin_url or "")
            github_url = st.text_input("GitHub Profile URL:", value=profile.github_url or "")
            portfolio_url = st.text_input("Portfolio / Website URL:", value=profile.portfolio_url or "")

        prof_summary = st.text_area("Master Professional Summary / Direction:", value=profile.professional_summary, height=100)

        submitted_ov = st.form_submit_button("💾 Save Profile Overview", use_container_width=True)
        if submitted_ov:
            if not full_name.strip():
                st.error("Full name cannot be empty.")
            else:
                profile.full_name = full_name.strip()
                profile.email = email.strip() or None
                profile.phone = phone.strip() or None
                profile.location = location.strip() or None
                profile.linkedin_url = linkedin_url.strip() or None
                profile.github_url = github_url.strip() or None
                profile.portfolio_url = portfolio_url.strip() or None
                profile.professional_summary = prof_summary.strip()
                CandidateService.save_active_profile(profile, change_summary="Updated contact & professional summary", changed_sections=["overview"])
                st.success("✓ Profile overview saved and synchronized with Candidate RAG!")
                st.rerun()

# -----------------------------------------------------------------------------
# TAB 2: Professional Experience (Full CRUD)
# -----------------------------------------------------------------------------
with tab_exp:
    st.subheader("💼 Professional Work Experience")
    st.caption("Add, edit, or remove verified client and production employment records. Total experience duration is calculated deterministically.")

    if profile.experiences:
        for idx, exp in enumerate(profile.experiences):
            with st.expander(f"🏢 {exp.title} — {exp.company} ({exp.start_date} – {exp.end_date})", expanded=False):
                with st.form(f"edit_exp_form_{exp.id}_{idx}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_company = st.text_input("Company*:", value=exp.company, key=f"e_comp_{idx}")
                        e_title = st.text_input("Job Title*:", value=exp.title, key=f"e_title_{idx}")
                        e_loc = st.text_input("Location:", value=exp.location or "", key=f"e_loc_{idx}")
                    with ec2:
                        e_start = st.text_input("Start Date (MM/YYYY)*:", value=exp.start_date, key=f"e_start_{idx}")
                        e_end = st.text_input("End Date (MM/YYYY or Present)*:", value=exp.end_date or "Present", key=f"e_end_{idx}")
                        e_current = st.checkbox("Current Employment", value=exp.is_current or (exp.end_date and exp.end_date.lower() == "present"), key=f"e_curr_{idx}")
                        e_tech = st.text_input("Technologies (comma-separated):", value=", ".join(exp.technologies_used), key=f"e_tech_{idx}")

                    e_resp_text = st.text_area(
                        "Responsibilities & Achievements (One per line):",
                        value="\n".join(exp.responsibilities),
                        height=120,
                        key=f"e_resp_{idx}",
                    )
                    e_metrics_text = st.text_input("Verified Metrics (comma-separated):", value=", ".join(exp.verified_metrics), key=f"e_met_{idx}")

                    btn_c1, btn_c2 = st.columns([3, 1])
                    with btn_c1:
                        sub_edit_exp = st.form_submit_button("💾 Save Experience Changes", use_container_width=True)
                    with btn_c2:
                        sub_del_exp = st.form_submit_button("🗑️ Delete Record", use_container_width=True)

                    if sub_edit_exp:
                        if not e_company.strip() or not e_title.strip() or not e_start.strip():
                            st.error("Company, Title, and Start Date are required.")
                        else:
                            exp.company = e_company.strip()
                            exp.title = e_title.strip()
                            exp.location = e_loc.strip() or None
                            exp.start_date = e_start.strip()
                            exp.end_date = "Present" if e_current else (e_end.strip() or "Present")
                            exp.is_current = e_current
                            exp.technologies_used = [t.strip() for t in e_tech.split(",") if t.strip()]
                            exp.responsibilities = [r.strip().lstrip("-*• ") for r in e_resp_text.splitlines() if r.strip()]
                            exp.verified_metrics = [m.strip() for m in e_metrics_text.split(",") if m.strip()]
                            CandidateService.update_experience(exp)
                            st.success(f"✓ Updated experience at '{exp.company}' successfully!")
                            st.rerun()

                    if sub_del_exp:
                        CandidateService.delete_experience(exp.id)
                        st.success(f"✓ Deleted experience at '{exp.company}'.")
                        st.rerun()
    else:
        st.info("No professional experience records registered yet.")

    st.markdown("---")
    st.markdown("#### ➕ Add New Professional Experience")
    with st.form("add_exp_form"):
        ae_c1, ae_c2 = st.columns(2)
        with ae_c1:
            ae_comp = st.text_input("Company Name*:", placeholder="e.g. Cognizant Technology Solutions")
            ae_title = st.text_input("Job Title*:", placeholder="e.g. Programmer Analyst")
            ae_loc = st.text_input("Location:", placeholder="e.g. Pune, India")
        with ae_c2:
            ae_start = st.text_input("Start Date (MM/YYYY)*:", placeholder="e.g. 11/2024")
            ae_end = st.text_input("End Date (MM/YYYY or Present)*:", placeholder="e.g. Present", value="Present")
            ae_curr = st.checkbox("Current Role", value=True)
            ae_tech = st.text_input("Technologies (comma-separated):", placeholder="e.g. Python, SQL, BigQuery, Airflow, GCP")

        ae_resp = st.text_area(
            "Responsibilities & Key Bullets (One per line)*:",
            placeholder="Built automated ETL pipelines in BigQuery.\nOptimized query compute costs by ~25% using clustering.",
            height=100,
        )
        ae_metrics = st.text_input("Verified Metrics (comma-separated):", placeholder="e.g. ~25% cost reduction, ~35% incident reduction")

        submit_add_exp = st.form_submit_button("💼 Add Professional Experience", use_container_width=True)
        if submit_add_exp:
            if not ae_comp.strip() or not ae_title.strip() or not ae_start.strip():
                st.error("Company Name, Job Title, and Start Date are required.")
            else:
                new_exp = Experience(
                    company=ae_comp.strip(),
                    title=ae_title.strip(),
                    location=ae_loc.strip() or None,
                    start_date=ae_start.strip(),
                    end_date="Present" if ae_curr else (ae_end.strip() or "Present"),
                    is_current=ae_curr,
                    technologies_used=[t.strip() for t in ae_tech.split(",") if t.strip()],
                    responsibilities=[r.strip().lstrip("-*• ") for r in ae_resp.splitlines() if r.strip()],
                    verified_metrics=[m.strip() for m in ae_metrics.split(",") if m.strip()],
                )
                try:
                    CandidateService.add_experience(new_exp)
                    st.success(f"✓ Added experience at '{ae_comp}' successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add experience: {e}")

# -----------------------------------------------------------------------------
# TAB 3: Projects (Full CRUD)
# -----------------------------------------------------------------------------
with tab_projects:
    st.subheader("🚀 Projects & Engineering Artifacts")
    st.caption("Personal projects are strictly isolated from client production experience.")

    if profile.projects:
        for idx, p in enumerate(profile.projects):
            with st.expander(f"📁 {p.name} [{p.project_type}]", expanded=False):
                with st.form(f"edit_proj_form_{p.id}_{idx}"):
                    ep_c1, ep_c2 = st.columns(2)
                    with ep_c1:
                        ep_name = st.text_input("Project Name*:", value=p.name, key=f"pname_{idx}")
                        ep_type = st.selectbox(
                            "Classification*:",
                            ["PERSONAL_PROJECT", "PROFESSIONAL_EXPERIENCE", "OPEN_SOURCE", "RESEARCH"],
                            index=["PERSONAL_PROJECT", "PROFESSIONAL_EXPERIENCE", "OPEN_SOURCE", "RESEARCH"].index(p.project_type) if p.project_type in ["PERSONAL_PROJECT", "PROFESSIONAL_EXPERIENCE", "OPEN_SOURCE", "RESEARCH"] else 0,
                            key=f"ptype_{idx}",
                        )
                        ep_tech = st.text_input("Technologies (comma-separated):", value=", ".join(p.technologies), key=f"ptech_{idx}")
                        ep_url = st.text_input("GitHub / Demo URL:", value=p.github_or_demo_url or "", key=f"purl_{idx}")
                    with ep_c2:
                        ep_desc = st.text_area("Description:", value=p.description, key=f"pdesc_{idx}", height=75)
                        ep_arch = st.text_input("Architecture Design:", value=p.architecture or "", key=f"parch_{idx}")
                        ep_outcome = st.text_input("Outcome / Results:", value=p.outcome or "", key=f"pout_{idx}")
                        ep_metrics = st.text_input("Metrics (comma-separated):", value=", ".join(p.metrics or p.verified_metrics), key=f"pmet_{idx}")

                    bullets_val = "\n".join(p.responsibilities or p.highlights or [])
                    ep_bullets = st.text_area("Highlight Bullets (One per line):", value=bullets_val, height=80, key=f"pbul_{idx}")

                    b_c1, b_c2 = st.columns([3, 1])
                    with b_c1:
                        sub_edit_proj = st.form_submit_button("💾 Save Project Changes", use_container_width=True)
                    with b_c2:
                        sub_del_proj = st.form_submit_button("🗑️ Delete Project", use_container_width=True)

                    if sub_edit_proj:
                        p.name = ep_name.strip()
                        p.project_type = ep_type
                        p.technologies = [t.strip() for t in ep_tech.split(",") if t.strip()]
                        p.description = ep_desc.strip()
                        p.architecture = ep_arch.strip() or None
                        p.outcome = ep_outcome.strip() or None
                        p.metrics = [m.strip() for m in ep_metrics.split(",") if m.strip()]
                        p.github_or_demo_url = ep_url.strip() or None
                        p.responsibilities = [b.strip().lstrip("-*• ") for b in ep_bullets.splitlines() if b.strip()]
                        p.highlights = p.responsibilities
                        CandidateService.update_project(p)
                        st.success(f"✓ Project '{p.name}' updated successfully!")
                        st.rerun()

                    if sub_del_proj:
                        CandidateService.delete_project(p.id)
                        st.success(f"✓ Deleted project '{p.name}'.")
                        st.rerun()
    else:
        st.info("No projects registered yet.")

    st.markdown("---")
    st.markdown("#### ➕ Add New Project")
    with st.form("add_project_form"):
        ap_c1, ap_c2 = st.columns(2)
        with ap_c1:
            p_name = st.text_input("Project Name*:", placeholder="e.g. Local RAG Sandbox")
            p_type = st.selectbox(
                "Project Classification*:",
                ["PERSONAL_PROJECT", "PROFESSIONAL_EXPERIENCE", "OPEN_SOURCE", "RESEARCH"],
                index=0,
            )
            p_tech = st.text_input("Technologies (comma-separated)*:", placeholder="e.g. Python, FAISS, BM25, Gemini API")
            p_url = st.text_input("GitHub / Demo URL (Optional):", placeholder="https://github.com/user/project")
        with ap_c2:
            p_desc = st.text_area("Project Description*:", placeholder="Overview of what the project does and its engineering objective.")
            p_arch = st.text_input("Architecture Design (Optional):", placeholder="e.g. Hybrid Dense-Sparse RRF Retrieval")
            p_outcome = st.text_input("Outcome / Key Results (Optional):", placeholder="e.g. Sub-100ms hybrid search latency")
            p_metrics = st.text_input("Key Metrics (Optional, comma-separated):", placeholder="e.g. ~92% accuracy, <5% false positive")

        p_bullets = st.text_area(
            "Responsibilities / Highlight Bullets (One per line):",
            placeholder="Built an anomaly detection system using BigQuery ML.\nIntegrated Gemini 2.5 Pro via Vertex AI for root-cause analysis.",
            height=80,
        )

        submit_proj = st.form_submit_button("🚀 Add Project to Profile", use_container_width=True)
        if submit_proj:
            if not p_name.strip() or not p_desc.strip():
                st.error("Project name and description are required.")
            else:
                tech_list = [t.strip() for t in p_tech.split(",") if t.strip()]
                metric_list = [m.strip() for m in p_metrics.split(",") if m.strip()]
                bullet_list = [b.strip().lstrip("-*• ") for b in p_bullets.splitlines() if b.strip()]
                new_proj = Project(
                    name=p_name.strip(),
                    project_type=p_type,
                    description=p_desc.strip(),
                    technologies=tech_list,
                    responsibilities=bullet_list,
                    highlights=bullet_list,
                    architecture=p_arch.strip() or None,
                    outcome=p_outcome.strip() or None,
                    metrics=metric_list,
                    github_or_demo_url=p_url.strip() or None,
                )
                try:
                    CandidateService.add_project(new_proj)
                    st.success(f"✓ Project '{p_name}' successfully added and indexed in Candidate RAG!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add project: {e}")

# -----------------------------------------------------------------------------
# TAB 4: Skills & Evidence (Full CRUD)
# -----------------------------------------------------------------------------
with tab_skills:
    st.subheader("🛠️ Technical Skills & Evidence Ledger")
    st.caption("Every skill maintains an explicit evidence level and verification status.")

    if profile.skills:
        skill_rows = []
        for s in profile.skills:
            skill_rows.append({
                "Skill": s.name,
                "Category": s.category.value if hasattr(s.category, "value") else str(s.category),
                "Evidence Level": s.evidence_level,
                "Status": "✅ VERIFIED" if s.evidence_status == "VERIFIED" else "⚠️ PARTIAL",
                "Proficiency": s.proficiency_level,
                "Years": s.years_of_experience or "N/A",
                "Context": s.context or "",
            })
        st.dataframe(pd.DataFrame(skill_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No skills registered.")

    st.markdown("---")
    s_col1, s_col2 = st.columns(2)

    with s_col1:
        st.markdown("#### ➕ Add Technical Skill")
        with st.form("add_skill_form"):
            sk_name = st.text_input("Skill Name*:", placeholder="e.g. LangGraph")
            sk_cat = st.selectbox(
                "Skill Category:",
                [c.value for c in SkillCategory],
                index=0,
            )
            sk_level = st.selectbox(
                "Evidence Level*:",
                ["PROFESSIONAL", "PERSONAL_PROJECT", "LEARNING_KNOWLEDGE"],
                index=0,
                help="PROFESSIONAL: Used in client/production. PERSONAL_PROJECT: Used in personal projects. LEARNING_KNOWLEDGE: Under study.",
            )
            sk_status = st.selectbox(
                "Verification Status*:",
                ["VERIFIED", "PARTIAL", "UNVERIFIED"],
                index=0,
            )
            sk_prof = st.selectbox(
                "Proficiency Level:",
                ["Beginner", "Intermediate", "Proficient", "Advanced", "Expert"],
                index=2,
            )
            sk_years = st.number_input("Years of Experience (Optional):", min_value=0.0, max_value=20.0, step=0.5, value=1.0)
            sk_ctx = st.text_input("Context / Usage Note (Optional):", placeholder="Used in automated data validation DAGs.")

            sub_skill = st.form_submit_button("➕ Add Skill", use_container_width=True)
            if sub_skill:
                if not sk_name.strip():
                    st.error("Skill name is required.")
                else:
                    new_skill = Skill(
                        name=sk_name.strip(),
                        category=SkillCategory(sk_cat),
                        evidence_level=sk_level,
                        evidence_status=sk_status,
                        proficiency_level=sk_prof,
                        years_of_experience=sk_years if sk_years > 0 else None,
                        context=sk_ctx.strip() or None,
                    )
                    try:
                        CandidateService.add_skill(new_skill)
                        st.success(f"✓ Skill '{sk_name}' added and synchronized!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add skill: {e}")

    with s_col2:
        st.markdown("#### 🗑️ Remove Skill")
        with st.form("del_skill_form"):
            skill_opts = [s.name for s in profile.skills]
            if skill_opts:
                del_target = st.selectbox("Select Skill to Remove:", skill_opts)
                sub_del_s = st.form_submit_button("🗑️ Remove Selected Skill", use_container_width=True)
                if sub_del_s:
                    CandidateService.delete_skill(del_target)
                    st.success(f"✓ Skill '{del_target}' removed.")
                    st.rerun()
            else:
                st.write("No skills to remove.")
                st.form_submit_button("Remove", disabled=True)

# -----------------------------------------------------------------------------
# TAB 5: Education (Full CRUD)
# -----------------------------------------------------------------------------
with tab_edu:
    st.subheader("🎓 Academic Credentials & Degrees")
    st.info("💡 The institution name, degree, graduation year, and CGPA stored here are canonical. The LLM cannot alter them.")

    if profile.education:
        for idx, edu in enumerate(profile.education):
            with st.expander(f"🎓 {edu.degree} in {edu.field_of_study} — {edu.institution} ({edu.graduation_year or 'N/A'})", expanded=True):
                with st.form(f"edit_edu_form_{idx}"):
                    ed_c1, ed_c2 = st.columns(2)
                    with ed_c1:
                        e_deg = st.text_input("Degree*:", value=edu.degree, key=f"ed_deg_{idx}")
                        e_field = st.text_input("Field of Study*:", value=edu.field_of_study, key=f"ed_field_{idx}")
                        e_inst = st.text_input("Institution / College*:", value=edu.institution, key=f"ed_inst_{idx}")
                    with ed_c2:
                        e_yr = st.text_input("Graduation Year*:", value=str(edu.graduation_year or "2024"), key=f"ed_yr_{idx}")
                        e_gpa = st.text_input("CGPA / Honors:", value=str(edu.gpa_or_honors or ""), key=f"ed_gpa_{idx}")

                    be_c1, be_c2 = st.columns([3, 1])
                    with be_c1:
                        sub_edit_edu = st.form_submit_button("💾 Save Education Changes", use_container_width=True)
                    with be_c2:
                        sub_del_edu = st.form_submit_button("🗑️ Delete Education", use_container_width=True)

                    if sub_edit_edu:
                        if not e_deg.strip() or not e_inst.strip():
                            st.error("Degree and Institution are required.")
                        else:
                            edu.degree = e_deg.strip()
                            edu.field_of_study = e_field.strip()
                            edu.institution = e_inst.strip()
                            edu.graduation_year = e_yr.strip() or None
                            edu.gpa_or_honors = e_gpa.strip() or None
                            CandidateService.update_education_entry(edu, index=idx)
                            st.success(f"✓ Education record for '{edu.institution}' updated successfully!")
                            st.rerun()

                    if sub_del_edu:
                        CandidateService.delete_education(edu.institution)
                        st.success(f"✓ Deleted education from '{edu.institution}'.")
                        st.rerun()
    else:
        st.info("No education records registered yet.")

    st.markdown("---")
    st.markdown("#### ➕ Add New Education Credential")
    with st.form("add_edu_form"):
        ae_c1, ae_c2 = st.columns(2)
        with ae_c1:
            n_deg = st.text_input("Degree*:", placeholder="e.g. B.Tech (Artificial Intelligence)")
            n_field = st.text_input("Field of Study*:", placeholder="e.g. Artificial Intelligence")
            n_inst = st.text_input("Institution / College*:", placeholder="e.g. G. H. Raisoni College of Engineering, Nagpur")
        with ae_c2:
            n_yr = st.text_input("Graduation Year*:", placeholder="e.g. 2024")
            n_gpa = st.text_input("CGPA / Honors:", placeholder="e.g. 8.83")

        submit_add_edu = st.form_submit_button("🎓 Add Education Record", use_container_width=True)
        if submit_add_edu:
            if not n_deg.strip() or not n_inst.strip():
                st.error("Degree and Institution are required.")
            else:
                new_edu = Education(
                    degree=n_deg.strip(),
                    field_of_study=n_field.strip(),
                    institution=n_inst.strip(),
                    graduation_year=n_yr.strip() or None,
                    gpa_or_honors=n_gpa.strip() or None,
                )
                CandidateService.add_education(new_edu)
                st.success(f"✓ Added education from '{n_inst}' successfully!")
                st.rerun()

# -----------------------------------------------------------------------------
# TAB 6: Certifications & Achievements (Full CRUD)
# -----------------------------------------------------------------------------
with tab_certs_achieve:
    st.subheader("🏆 Certifications & Key Achievements")

    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("#### 📜 Certifications")
        if profile.certifications:
            for c_idx, cert in enumerate(profile.certifications):
                with st.container():
                    st.markdown(f"• **{cert}**")
                    if st.button("🗑️ Remove", key=f"del_cert_{c_idx}"):
                        CandidateService.delete_certification(cert)
                        st.success(f"✓ Removed certification: {cert}")
                        st.rerun()
        else:
            st.info("No certifications registered.")

        st.markdown("---")
        with st.form("add_cert_form"):
            new_cert_name = st.text_input("Add Certification*:", placeholder="e.g. Google Cloud Certified Associate Data Practitioner")
            if st.form_submit_button("➕ Add Certification", use_container_width=True):
                if new_cert_name.strip():
                    try:
                        CandidateService.add_certification(new_cert_name.strip())
                        st.success(f"✓ Added certification: {new_cert_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with c_col2:
        st.markdown("#### 🏆 Key Career Achievements")
        ach_items = getattr(profile, "achievements", [])
        if ach_items:
            for a_idx, ach in enumerate(ach_items):
                with st.expander(f"🌟 {ach.title}", expanded=False):
                    st.markdown(f"**Description:** {ach.description}")
                    if ach.metrics:
                        st.markdown(f"**Metrics:** `{ach.metrics}`")
                    if st.button("🗑️ Delete Achievement", key=f"del_ach_{ach.id}_{a_idx}"):
                        CandidateService.delete_achievement(ach.id)
                        st.success(f"✓ Deleted achievement: {ach.title}")
                        st.rerun()
        else:
            st.info("No achievements registered.")

        st.markdown("---")
        with st.form("add_ach_form"):
            a_title = st.text_input("Achievement Title*:", placeholder="e.g. AI Data Quality Anomaly Detection")
            a_desc = st.text_area("Achievement Description*:", placeholder="Achieved 92% anomaly detection accuracy on BigQuery pipelines.")
            a_met = st.text_input("Key Metrics:", placeholder="e.g. 92% accuracy, <5% false positive")
            if st.form_submit_button("🏆 Add Achievement", use_container_width=True):
                if a_title.strip() and a_desc.strip():
                    new_ach = Achievement(
                        title=a_title.strip(),
                        description=a_desc.strip(),
                        metrics=a_met.strip() or None,
                    )
                    CandidateService.add_achievement(new_ach)
                    st.success(f"✓ Added achievement: {a_title}")
                    st.rerun()
                else:
                    st.error("Title and Description are required.")

# -----------------------------------------------------------------------------
# TAB 7: Preferences
# -----------------------------------------------------------------------------
with tab_pref:
    st.subheader("🎯 Career Goals & Application Preferences")
    with st.form("career_pref_form"):
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            available_roles = [r.value for r in RoleCategory]
            curr_roles = [r.value if hasattr(r, "value") else str(r) for r in profile.preferences.target_roles]
            target_roles = st.multiselect(
                "Target Role Categories*:",
                available_roles,
                default=[r for r in curr_roles if r in available_roles],
                placeholder="Select one or more target roles",
            )
            sen_options = [s.value for s in SeniorityLevel]
            curr_sen = profile.preferences.preferred_seniority.value if hasattr(profile.preferences.preferred_seniority, "value") else str(profile.preferences.preferred_seniority)
            pref_sen = st.selectbox("Target Seniority Level:", sen_options, index=sen_options.index(curr_sen) if curr_sen in sen_options else 0)
            pref_modes = st.multiselect("Work Mode Preferences:", ["Remote", "Hybrid", "On-site"], default=profile.preferences.work_modes or ["Remote", "Hybrid"])

        with p_c2:
            pref_locs = st.text_input("Target Locations (comma-separated):", value=", ".join(profile.preferences.target_locations or []), placeholder="e.g. Pune, Bangalore, Remote")
            pref_comp = st.text_input("Target Compensation (Optional):", value=profile.preferences.min_desired_comp or "", placeholder="e.g. 9-10 LPA")
            pref_clouds = st.multiselect("Cloud Ecosystem Preferences:", ["GCP", "AWS", "Azure", "Multi-cloud"], default=profile.preferences.cloud_preferences or [])


        sub_pref = st.form_submit_button("💾 Save Career Preferences", use_container_width=True)
        if sub_pref:
            new_pref = CareerPreference(
                target_roles=[RoleCategory(r) for r in target_roles],
                preferred_seniority=SeniorityLevel(pref_sen),
                work_modes=pref_modes,
                target_locations=[l.strip() for l in pref_locs.split(",") if l.strip()],
                min_desired_comp=pref_comp.strip() or None,
                cloud_preferences=pref_clouds,
            )
            CandidateService.update_preferences(new_pref)
            st.success("✓ Career preferences saved!")
            st.rerun()

# -----------------------------------------------------------------------------
# TAB 8: External Profiles (GitHub, LinkedIn, Naukri)
# -----------------------------------------------------------------------------
with tab_external:
    st.subheader("🌐 External Profile Integrations")
    st.caption("Official connectors and zero-scraping manual ingest for GitHub, LinkedIn, and Naukri.")

    ext_sub1, ext_sub2, ext_sub3 = st.tabs(["🐙 GitHub", "💼 LinkedIn", "📄 Naukri"])

    with ext_sub1:
        st.markdown("#### 🐙 Official GitHub Integration")
        st.markdown("Connects to public repositories via official GitHub REST API with SSL certificate validation.")
        st.info("💡 All ingested repositories are classified as `PERSONAL_PROJECT` candidate evidence upon user approval.")

        gh_url = profile.github_url or ""
        default_gh_user = gh_url.rstrip("/").split("/")[-1] if gh_url else ""

        c_gh1, c_gh2 = st.columns([2, 1])
        with c_gh1:
            gh_user_input = st.text_input(
                "GitHub Username or Profile URL:",
                value=default_gh_user,
                placeholder="e.g. your-github-username",
                help="Enter your GitHub username or profile URL to sync public repositories.",
            ).strip()
            resolved_gh = gh_user_input.rstrip("/").split("/")[-1] if gh_user_input else ""
            if resolved_gh:
                st.caption(f"🌐 Target Profile: [https://github.com/{resolved_gh}](https://github.com/{resolved_gh})")
        with c_gh2:

            st.write("")
            st.write("")
            sync_gh_btn = st.button("🔄 Sync GitHub Repositories", type="primary", use_container_width=True, disabled=not bool(gh_user_input))

        if sync_gh_btn and gh_user_input:
            with st.spinner(f"Fetching public repositories from GitHub API for '{resolved_gh}'..."):
                from careerpilot.integrations.github_connector import GitHubConnector
                gh_result = GitHubConnector.sync_github_profile(resolved_gh)
                if gh_result["status"] == "SUCCESS":
                    st.session_state["github_synced_repos"] = gh_result["repos"]
                    st.success(f"✓ Successfully fetched {gh_result['repos_count']} public repositories from GitHub for user '{resolved_gh}'!")
                else:
                    st.error(f"GitHub Sync Failed: {gh_result.get('error')}")

        if "github_synced_repos" in st.session_state:
            repos = st.session_state["github_synced_repos"]
            st.markdown(f"##### Repositories Awaiting Review ({len(repos)})")
            for idx, r in enumerate(repos):
                with st.expander(f"📦 {r['name']} — {r['language']} (⭐ {r['stars']})", expanded=(idx < 2)):
                    st.markdown(f"**Description:** {r['description'] or 'No description provided'}")
                    st.markdown(f"**URL:** [{r['html_url']}]({r['html_url']})")
                    st.markdown(f"**Classification:** `{r['classification']}`")
                    if r.get("topics"):
                        st.markdown(f"**Topics:** {', '.join(r['topics'])}")

                    if st.button(f"✅ Approve & Ingest as Project Evidence", key=f"app_gh_{r['name']}"):
                        from careerpilot.integrations.github_connector import GitHubConnector
                        ok = GitHubConnector.approve_and_import_project(r)
                        if ok:
                            st.success(f"✓ Project '{r['name']}' approved and saved to Candidate Evidence Ledger!")
                            st.rerun()

    with ext_sub2:
        st.markdown("#### 💼 LinkedIn Integration (Zero-Scraping Policy)")
        from careerpilot.integrations.linkedin_connector import LinkedInConnector
        li_status = LinkedInConnector.get_status()
        st.markdown(f"- **Profile URL:** [{li_status['profile_url']}]({li_status['profile_url']})")
        st.markdown(f"- **API Tier:** `{li_status['api_tier']}`")
        st.markdown(f"- **Scraping Policy:** `{li_status['scraping_policy']}`")

        with st.expander("ℹ️ Why Direct URL Scraping is Disabled & API Limitations"):
            st.info(
                "**Why can't CareerPilot scrape directly from a URL?**\n"
                "LinkedIn strictly blocks automated web crawlers (returning HTTP 999 errors) and prohibits scraping under its Terms of Service. "
                "Furthermore, LinkedIn's public Developer API (`r_liteprofile`) does not share member work experience or skills without a paid Enterprise Talent Solutions partnership.\n\n"
                "To protect your account and maintain 100% legal compliance, CareerPilot supports **3 official and convenient import methods** below."
            )
            for f_name, expl in li_status["api_field_limitations"].items():
                st.warning(f"**{f_name.replace('_', ' ').title()}:** {expl}")

        st.markdown("---")
        li_opt1, li_opt2, li_opt3 = st.tabs([
            "⚡ 1. LinkedIn Profile PDF (Fastest)",
            "📝 2. Paste Profile Text",
            "📁 3. Official CSV Archive",
        ])

        with li_opt1:
            st.markdown("##### ⚡ Instant Ingestion via LinkedIn Profile PDF")
            st.caption(
                "**How to get this in 10 seconds:**\n"
                "1. Open your LinkedIn profile in any browser.\n"
                "2. Click the **'More'** button (next to 'Open to' / 'Add section') on your profile header.\n"
                "3. Select **'Save to PDF'**.\n"
                "4. Upload that PDF file here."
            )
            li_pdf_file = st.file_uploader("Upload LinkedIn Profile PDF:", type=["pdf"], key="li_pdf_upload")
            if li_pdf_file and st.button("🚀 Parse & Import LinkedIn PDF", key="li_pdf_btn", type="primary"):
                with st.spinner("Extracting and validating LinkedIn profile details..."):
                    pdf_bytes = li_pdf_file.read()
                    res = LinkedInConnector.parse_linkedin_pdf(pdf_bytes)
                    if res["status"] == "SUCCESS":
                        st.success(f"✓ Successfully imported {res['imported_count']} verified items from LinkedIn Profile PDF!")
                        st.rerun()
                    else:
                        st.error("Failed to parse LinkedIn PDF.")

        with li_opt2:
            st.markdown("##### 📝 Paste LinkedIn Profile Text Directly")
            st.caption("Copy-paste sections from your LinkedIn profile (e.g. About summary, Experience descriptions, or Skills).")
            paste_sec = st.selectbox("Section Type:", ["experience", "skills", "summary"], key="li_paste_sec")
            li_paste_text = st.text_area("Paste LinkedIn Text Here:", height=140, key="li_paste_text")
            if st.button("📥 Import Pasted LinkedIn Text", key="li_paste_btn"):
                if li_paste_text.strip():
                    cnt = LinkedInConnector.import_manual_profile_text(li_paste_text, section=paste_sec)
                    st.success(f"✓ Ingested {cnt} facts with verified LinkedIn provenance!")
                    st.rerun()
                else:
                    st.error("Please paste text before importing.")

        with li_opt3:
            st.markdown("##### 📁 Import Official LinkedIn Data Export Archive")
            st.caption("Upload candidate's downloaded LinkedIn data archive CSV (e.g. `Positions.csv` or `Skills.csv`).")
            li_file = st.file_uploader("Upload LinkedIn CSV Export:", type=["csv"], key="li_csv_upload")
            li_section = st.selectbox("Archive Section:", ["positions", "skills"], key="li_section_sel")
            if li_file and st.button("📥 Parse & Import LinkedIn CSV", key="li_import_btn"):
                content = li_file.read().decode("utf-8", errors="ignore")
                imported = LinkedInConnector.parse_manual_csv_export(content, section=li_section)
                st.success(f"✓ Successfully imported {len(imported)} verified items with LinkedIn provenance!")
                st.rerun()

    with ext_sub3:
        st.markdown("#### 📄 Naukri Integration (Zero-Scraping Policy)")
        from careerpilot.integrations.naukri_connector import NaukriConnector
        nk_status = NaukriConnector.get_status()
        st.info(f"ℹ️ **Status:** {nk_status['message']}")
        st.markdown(f"- **Scraping Policy:** `{nk_status['scraping_policy']}`")

        st.markdown("---")
        st.markdown("##### 📝 Manual Naukri Profile / Experience Ingest")
        st.caption("Paste text from your Naukri profile or job application summary. CareerPilot will parse and record it with verified Naukri provenance.")
        nk_text = st.text_area("Paste Naukri Profile Text:", height=150, key="nk_text_area")
        if st.button("📥 Ingest Naukri Profile Text", key="nk_import_btn"):
            if nk_text.strip():
                count = NaukriConnector.import_manual_profile_text(nk_text)
                st.success(f"✓ Ingested {count} candidate facts from Naukri text!")
                st.rerun()
            else:
                st.error("Please paste profile text before importing.")

# -----------------------------------------------------------------------------
# TAB 9: Master Resume Import & Change Review
# -----------------------------------------------------------------------------
with tab_import:
    st.subheader("📥 Master Resume Import & Change Review")
    st.caption("Upload a new master resume PDF or DOCX to detect differences and selectively merge changes.")

    uploaded_resume = st.file_uploader("Upload New Master Resume (PDF or DOCX):", type=["pdf", "docx"])

    if uploaded_resume:
        if st.button("🔍 Parse & Review Detected Changes", use_container_width=True):
            with st.spinner("Extracting and computing differences..."):
                raw_text = ResumeImportService.extract_text(uploaded_resume.getvalue(), filename=uploaded_resume.name)
                parsed_data = ResumeImportService.parse_resume_content(raw_text)
                diff_res = ResumeImportService.compute_diff(profile, parsed_data)
                st.session_state["resume_diff_result"] = diff_res
                st.session_state["parsed_resume_text"] = raw_text

    if "resume_diff_result" in st.session_state:
        diff_res = st.session_state["resume_diff_result"]
        d_c1, d_c2, d_c3, d_c4 = st.columns(4)
        with d_c1:
            st.metric("New Elements (ADDED)", diff_res.total_added)
        with d_c2:
            st.metric("Removed Elements", diff_res.total_removed)
        with d_c3:
            st.metric("Changed Elements", diff_res.total_changed)
        with d_c4:
            st.metric("Unchanged Elements", diff_res.total_unchanged)

        if diff_res.diff_items:
            st.markdown("#### Detected Changes")
            with st.form("apply_diff_form"):
                approved_items = []
                for idx, item in enumerate(diff_res.diff_items):
                    if item.change_type == "ADDED":
                        checked = st.checkbox(f"➕ **[NEW]** {item.item_name}", value=True, key=f"diff_chk_{idx}")
                        item.approved = checked
                        approved_items.append(item)
                    elif item.change_type == "UNCHANGED":
                        st.caption(f"⚪ **[MATCH]** {item.item_name}")

                sub_apply = st.form_submit_button("✅ Merge Approved Changes into Profile", use_container_width=True)
                if sub_apply:
                    ResumeImportService.apply_diff_items(profile, approved_items)
                    del st.session_state["resume_diff_result"]
                    st.success("✓ Approved changes merged and candidate evidence updated!")
                    st.rerun()
        else:
            st.info("No differences detected between uploaded resume and active profile.")

# -----------------------------------------------------------------------------
# TAB 9: Profile Version History & Rollback
# -----------------------------------------------------------------------------
with tab_history:
    st.subheader("🕒 Profile Version History & Rollback")
    st.caption("Every approved update creates a snapshot. You can restore any past version with one click.")

    versions = CandidateService.list_profile_versions()
    if versions:
        v_list = []
        for v in versions:
            v_list.append({
                "Version": v.version_tag,
                "Change Summary": v.change_summary,
                "Sections Changed": ", ".join(v.changed_sections_json or []),
                "Created At": format_datetime(v.created_at),
                "Version ID": v.id,
            })
        st.dataframe(pd.DataFrame(v_list), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### ⏪ Rollback to Previous Version")
        v_choice_dict = {f"{v.version_tag} — {v.change_summary} [{format_datetime(v.created_at)}]": v.id for v in versions}
        selected_v_label = st.selectbox("Select Version to Restore:", list(v_choice_dict.keys()))

        if st.button("⏪ Restore Selected Version", type="primary", use_container_width=True):
            target_vid = v_choice_dict[selected_v_label]
            with st.spinner("Restoring profile version..."):
                restored_prof = CandidateService.restore_profile_version(target_vid)
                st.success(f"✓ Profile successfully restored to {selected_v_label} and Candidate RAG re-synchronized!")
                st.rerun()
    else:
        st.info("No profile version snapshots recorded yet.")
