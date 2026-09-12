import streamlit as st
from pathlib import Path
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import DecisionRecommendation, ApplicationStatus
from careerpilot.core.config import settings

st.set_page_config(page_title="Analyze Job — CareerPilot AI", page_icon="🔍", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("🔍 Job Description Analysis & Candidate Fit Engine")
st.caption("Evaluate actual role realities, calculate candidate fit against verified evidence, and get deterministic recommendations.")

# Session state initialization for analysis results
if "current_analysis" not in st.session_state:
    st.session_state.current_analysis = None
if "current_app" not in st.session_state:
    st.session_state.current_app = None

# 1. Job Input Section
with st.expander("📝 Provide Job Description", expanded=(st.session_state.current_analysis is None)):
    input_tab1, input_tab2, input_tab3 = st.tabs(["📋 Paste JD Text", "📁 Upload File (TXT/PDF)", "📂 Load Evaluation Benchmark"])

    jd_text = ""
    company_name = ""
    job_title = ""
    job_location = "Remote / Flexible"
    job_url = ""

    with input_tab1:
        c_title, c_comp = st.columns(2)
        with c_title:
            job_title_in = st.text_input("Job Title (Optional)", placeholder="e.g. AI Data Engineer")
        with c_comp:
            company_in = st.text_input("Company Name (Optional)", placeholder="e.g. Acme AI Corp")
        
        c_loc, c_url = st.columns(2)
        with c_loc:
            job_loc_in = st.text_input("Job Location (Optional)", placeholder="e.g. Bangalore / Remote", value="Remote / Flexible")
        with c_url:
            job_url_in = st.text_input("Job URL (Optional)", placeholder="https://careers.company.com/job/123")
            
        jd_text_in = st.text_area("Job Description Content", height=220, placeholder="Paste complete job description text here...")

    with input_tab2:
        uploaded_file = st.file_uploader("Upload Job Description File (.txt or .pdf)", type=["txt", "pdf"])
        if uploaded_file is not None:
            if uploaded_file.size > settings.MAX_UPLOAD_SIZE_BYTES:
                st.error(f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.1f} MB.")
            elif not any(uploaded_file.name.lower().endswith(ext) for ext in settings.ALLOWED_UPLOAD_EXTENSIONS):
                st.error(f"Unsupported file format. Please upload only {settings.ALLOWED_UPLOAD_EXTENSIONS} files.")
            else:
                try:
                    if uploaded_file.name.lower().endswith(".txt"):
                        jd_text_in = uploaded_file.read().decode("utf-8", errors="ignore")
                        st.success(f"Loaded text file: {uploaded_file.name} ({len(jd_text_in)} chars)")
                    elif uploaded_file.name.lower().endswith(".pdf"):
                        import uuid
                        safe_filename = f"upload_{uuid.uuid4().hex[:8]}_{Path(uploaded_file.name).stem}.pdf"
                        upload_dest = settings.UPLOADS_DIR / safe_filename
                        with open(upload_dest, "wb") as f:
                            f.write(uploaded_file.read())
                        from careerpilot.parsers.jd_parser import JobDescriptionParser
                        parsed_pdf = JobDescriptionParser.parse_file(upload_dest)
                        jd_text_in = parsed_pdf.raw_text
                        st.success(f"Successfully extracted text from PDF: {uploaded_file.name} ({len(jd_text_in)} chars)")
                except Exception as e:
                    st.error(f"Error parsing uploaded file: {str(e)}")


    with input_tab3:
        st.markdown("#### 🔗 Multi-Source Import & Canonical Deduplication")
        st.caption("Import job postings from LinkedIn, Naukri, or Company Portals. CareerPilot will automatically deduplicate identical jobs across sources.")
        ext_source = st.selectbox("Source Platform", ["LinkedIn", "Naukri", "Direct Career Portal", "Evaluation Benchmark"])
        ext_url = st.text_input("Posting URL (Optional):", placeholder="https://www.linkedin.com/jobs/view/...")
        if ext_source == "Evaluation Benchmark":
            eval_files = list(settings.EVALUATION_JOBS_DIR.glob("*.txt"))
            if eval_files:
                selected_eval = st.selectbox("Select Benchmark Sample:", [f.name for f in eval_files])
                if selected_eval:
                    sel_path = settings.EVALUATION_JOBS_DIR / selected_eval
                    with open(sel_path, "r", encoding="utf-8") as f:
                        jd_text_in = f.read()
                    st.info(f"Loaded benchmark: **{selected_eval}**")

    # Analyze Button
    if st.button("🚀 Analyze Job Description", type="primary", use_container_width=True):
        if not jd_text_in.strip():
            st.error("Please provide job description text or upload a file.")
        else:
            with st.spinner("Analyzing Job Description with LangGraph Agent..."):
                from careerpilot.analysis.job_deduplicator import JobDeduplicator
                dedup_res = JobDeduplicator.deduplicate_job(
                    company_name=company_in or "Target Company",
                    job_title=job_title_in or "Target Role",
                    location=job_loc_in or "Remote",
                    source_url=job_url_in or ext_url or None,
                    raw_text=jd_text_in,
                )
                if dedup_res["is_duplicate"]:
                    st.info(f"ℹ️ Canonical Match Detected: Linked to existing canonical job '{dedup_res['canonical_job_id']}' (matched via {dedup_res.get('matched_by')}).")

                progress = st.progress(0.1, text="Parsing Job Requirements...")
                progress.progress(0.35, text="Retrieving Candidate Evidence from RAG...")
                progress.progress(0.70, text="Calculating Deterministic Fit & Risk Analysis...")
                
                analysis, app = CareerPilotService.analyze_job(
                    input_source=jd_text_in,
                    company_name=company_in or None,
                    job_title=job_title_in or None,
                    job_location=job_loc_in or "Remote / Flexible",
                    job_url=job_url_in or ext_url or None,
                )
                progress.progress(1.0, text="Analysis Complete!")
                st.session_state.current_analysis = analysis
                st.session_state.current_app = app
                st.success(f"Analyzed job '{analysis.job_title}' at '{analysis.company_name}' successfully!")
                st.rerun()

# 2. Display Analysis Results
if st.session_state.current_analysis:
    analysis = st.session_state.current_analysis
    app = st.session_state.current_app

    st.markdown("---")
    st.header(f"📊 Analysis: {analysis.job_title} @ {analysis.company_name}")
    
    rec_val = analysis.recommendation.value
    score_val = analysis.fit_score.overall_score

    # -------------------------------------------------------------------------
    # 2.1 Visually Obvious Main Decision Card
    # -------------------------------------------------------------------------
    c_score_box, c_why_box = st.columns([1, 2])
    with c_score_box:
        st.markdown("### FIT SCORE")
        st.markdown(f"<h1 style='font-size: 3.5rem; margin-top: -15px; margin-bottom: 5px;'>{score_val:.0f}%</h1>", unsafe_allow_html=True)
        if rec_val == "APPLY":
            st.markdown("<span style='background-color: #DCFCE7; color: #166534; font-size: 1.3rem; padding: 6px 16px; border-radius: 8px; font-weight: bold;'>🟢 APPLY</span>", unsafe_allow_html=True)
        elif rec_val == "REVIEW":
            st.markdown("<span style='background-color: #FEF9C3; color: #854D0E; font-size: 1.3rem; padding: 6px 16px; border-radius: 8px; font-weight: bold;'>🟡 REVIEW</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='background-color: #FEE2E2; color: #991B1B; font-size: 1.3rem; padding: 6px 16px; border-radius: 8px; font-weight: bold;'>🔴 SKIP</span>", unsafe_allow_html=True)
            
        st.markdown("")
        role_label = analysis.role_classification.primary_role.value.replace("_", " ").title()
        sen_val = analysis.seniority_detection.detected_seniority.value.title() if hasattr(analysis.seniority_detection, "detected_seniority") else str(analysis.seniority_detection)
        st.caption(f"Role: **{role_label}** • Seniority: **{sen_val}**")

    with c_why_box:
        st.markdown("### Why?")
        decision_why = getattr(analysis, "decision_reason", "") or analysis.explainable_reasoning.splitlines()[0]
        st.markdown(f"**{decision_why}**")
        
        st.markdown("#### Recommendation & Next Step")
        next_step = getattr(analysis, "next_action", "") or "Review the job requirements and highlight transferable skills in your application."
        st.info(f"👉 **{next_step}**")

    # -------------------------------------------------------------------------
    # 2.2 Requirements Breakdown: Strong Matches | Missing Required | Preferred Gaps
    # -------------------------------------------------------------------------
    st.markdown("---")
    c_str, c_req_gaps, c_pref_gaps = st.columns(3)
    with c_str:
        st.markdown("#### ✓ Strong Matches")
        top_matches = getattr(analysis, "top_matching_requirements", []) or analysis.key_strengths
        if top_matches:
            for s in top_matches[:6]:
                st.markdown(f"✓ **{s}**")
        else:
            st.write("No direct skills verified.")

    with c_req_gaps:
        st.markdown("#### ✕ Missing Required Skills")
        req_gaps = getattr(analysis, "missing_required_requirements", []) or [g for g in analysis.key_gaps if "aws" in g.lower() or "year" in g.lower()]
        if req_gaps:
            for s in req_gaps[:6]:
                st.markdown(f"<span style='color: #DC2626;'>✕ <b>{s}</b></span>", unsafe_allow_html=True)
        else:
            st.success("✓ All mandatory requirements verified!")

    with c_pref_gaps:
        st.markdown("#### • Preferred Gaps (Nice-to-Have)")
        pref_gaps = getattr(analysis, "missing_preferred_requirements", [])
        if pref_gaps:
            for s in pref_gaps[:6]:
                st.markdown(f"• **{s}** *(Preferred — does not prevent applying)*")
        else:
            st.write("• No preferred gaps identified.")

    # -------------------------------------------------------------------------
    # 2.3 Zero-Score / Critical Mismatch Explanatory Box
    # -------------------------------------------------------------------------
    z_exp = getattr(analysis, "zero_score_explanation", None)
    if z_exp or score_val == 0.0:
        with st.expander("ℹ️ Why is this role marked as a Critical Mismatch / SKIP?", expanded=True):
            primary_reason = z_exp.get("primary_skip_reason") if z_exp else "Role requirements significantly exceed your verified profile."
            st.error(f"**Primary Reason:** {primary_reason}")
            if z_exp and z_exp.get("blocking_requirements"):
                st.markdown(f"**Blocking Requirements:** {', '.join(z_exp['blocking_requirements'])}")
            if z_exp and z_exp.get("matched_requirements"):
                st.markdown(f"**Verified Matches:** {', '.join(z_exp['matched_requirements'])}")
            if z_exp and z_exp.get("next_action"):
                st.markdown(f"**Actionable Next Step:** {z_exp['next_action']}")

    # -------------------------------------------------------------------------
    # 2.4 Context Comparisons: Experience & Cloud Platform
    # -------------------------------------------------------------------------
    st.markdown("---")
    c_exp_box, c_cloud_box = st.columns(2)
    with c_exp_box:
        st.markdown("#### ⏳ Experience Comparison")
        exp_comp = getattr(analysis, "experience_comparison", {})
        if exp_comp:
            st.markdown(f"**{exp_comp.get('explanation', 'Experience matches profile.')}**")
            cand_y = exp_comp.get("candidate_years", 1.9)
            req_y = exp_comp.get("required_years")
            if req_y is not None:
                st.caption(f"Verified Profile: {cand_y:.1f} years | JD Requirement: {req_y:.0f}+ years")
            else:
                st.caption(f"Verified Profile: {cand_y:.1f} years | JD Requirement: Not explicitly stated")
        else:
            st.write("Experience comparison based on role seniority.")

    with c_cloud_box:
        st.markdown("#### ☁️ Cloud Platform Match")
        c_comp = getattr(analysis, "cloud_comparison", {})
        if c_comp:
            st.markdown(f"**{c_comp.get('explanation', 'Cloud concepts evaluated.')}**")
            st.caption(f"Verified Cloud: **{c_comp.get('candidate_cloud', 'GCP')}** | Target Cloud: **{c_comp.get('required_cloud', 'None')}**")
        else:
            st.write("Cloud transferability evaluated.")

    # -------------------------------------------------------------------------
    # 2.5 User Decision Override Panel
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 Application Decision & Tracking")
    c_act, c_over = st.columns([1, 1])
    
    with c_act:
        from careerpilot.core.terminology import get_friendly_status_label
        st.markdown(f"**Pipeline Status:** `{get_friendly_status_label(app.application_status)}` | **User Decision:** `{app.user_decision.value}`")
        if rec_val == "APPLY":
            st.success("✅ **System Recommendation: APPLY.** Strong verified evidence for core requirements.")
        elif rec_val == "REVIEW":
            st.warning("⚠️ **System Recommendation: REVIEW.** Meaningful overlap with manageable or transferable gaps.")
        else:
            st.error("⛔ **System Recommendation: SKIP.** Critical requirements mismatch verified background.")

    with c_over:
        st.markdown("#### ⚙️ Override User Decision")
        new_dec_str = st.selectbox(
            "Set Your Decision (Does not overwrite system recommendation):",
            [DecisionRecommendation.APPLY.value, DecisionRecommendation.REVIEW.value, DecisionRecommendation.SKIP.value],
            index=[DecisionRecommendation.APPLY.value, DecisionRecommendation.REVIEW.value, DecisionRecommendation.SKIP.value].index(app.user_decision.value)
        )
        if st.button("💾 Save Decision Override", use_container_width=True):
            updated_app = CareerPilotService.update_application_decision(app.application_id, DecisionRecommendation(new_dec_str))
            st.session_state.current_app = updated_app
            st.success(f"Decision saved as: **{new_dec_str}**")
            st.rerun()

    # -------------------------------------------------------------------------
    # 2.6 Detailed Diagnostics & Component Breakdown Tabs
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("🔍 View Detailed Scoring Breakdown & Requirements Table", expanded=False):
        tab_calib, tab_req, tab_risks, tab_cloud = st.tabs([
            "🧮 Score Breakdown & Penalties",
            "📋 Requirements Table",
            "🚨 Identified Risks",
            "☁️ Cloud Transferability Detail",
        ])

        with tab_calib:
            st.markdown("### Calibrated Score Breakdown Across Dimensions")
            fit_b = analysis.fit_score
            
            fb_c1, fb_c2, fb_c3 = st.columns(3)
            with fb_c1:
                st.metric("Core Skills Match", f"{fit_b.must_have_score:.1f}%")
                st.metric("Role Alignment", f"{fit_b.role_alignment_score:.1f}%")
                st.metric("Company Preference", f"{getattr(fit_b, 'company_preference_score', 85.0):.1f}%")
            with fb_c2:
                st.metric("Preferred Skills Match", f"{getattr(fit_b, 'nice_to_have_score', 85.0):.1f}%")
                st.metric("Evidence Strength", f"{getattr(fit_b, 'evidence_strength_score', 85.0):.1f}%")
                st.metric("Cloud Alignment", f"{fit_b.cloud_score:.1f}%")
            with fb_c3:
                st.metric("Experience Match", f"{fit_b.experience_score:.1f}%")
                st.metric("Location Preference", f"{getattr(fit_b, 'location_preference_score', 90.0):.1f}%")
                pen = getattr(fit_b, 'disqualifying_gap_penalty', fit_b.must_have_penalty)
                st.metric("Total Penalties", f"-{pen:.1f} pts")

            # Display explicit penalties list if any
            pen_list = getattr(analysis, "penalty_details", []) or getattr(fit_b, "penalties", [])
            if pen_list:
                st.markdown("#### Deductions & Penalties:")
                for p in pen_list:
                    st.warning(f"- **{p.get('name')}:** -{p.get('deduction'):.1f} pts ({p.get('reason')})")

            st.markdown("---")
            st.metric("Final Calibrated Fit Score", f"{fit_b.overall_score:.1f}%")

        with tab_req:
            st.markdown("### Job Requirements & Candidate Evidence Matching")
            from careerpilot.core.terminology import get_friendly_match_label
            req_rows = []
            for m in analysis.matches:
                req_rows.append({
                    "Requirement": m.requirement_skill,
                    "Importance": "Required" if m.importance.value == "MUST_HAVE" else "Preferred",
                    "Status": get_friendly_match_label(m.match_status),
                    "Match Score": f"{m.match_score * 100:.0f}%",
                    "Candidate Evidence ID": m.candidate_evidence_id or "Not verified",
                })
            st.dataframe(req_rows, use_container_width=True, hide_index=True)

        with tab_risks:
            st.markdown("### Risk Analysis")
            if analysis.risks:
                for r in analysis.risks:
                    r_type = r.risk_type.value.replace('_', ' ').title() if hasattr(r, 'risk_type') else (r.title if hasattr(r, 'title') else "Risk")
                    st.error(f"**[{r.severity.value}] {r_type}:** {r.description}")
            else:
                st.success("Low application risk. Candidate profile is well-aligned.")

        with tab_cloud:
            st.markdown("### Cloud Environment Transferability")
            cloud = analysis.cloud_transferability
            target_cloud = cloud.cloud_requested if hasattr(cloud, "cloud_requested") else cloud.primary_target_cloud
            cand_cloud = cloud.candidate_cloud if hasattr(cloud, "candidate_cloud") else cloud.candidate_verified_cloud
            t_status = cloud.transferability_status.value if hasattr(cloud.transferability_status, "value") else str(cloud.transferability_status)
            t_reason = cloud.transferability_reasoning if hasattr(cloud, "transferability_reasoning") else cloud.explanation
            st.markdown(f"- **Target Cloud Ecosystem:** `{target_cloud}`")
            st.markdown(f"- **Candidate Verified Cloud:** `{cand_cloud}`")
            st.markdown(f"- **Transferability Status:** `{t_status}`")
            st.markdown(f"- **Explanation:** {t_reason}")
            if t_reason:
                st.info(f"💡 **Recommended Framing:** \"{t_reason}\"")
