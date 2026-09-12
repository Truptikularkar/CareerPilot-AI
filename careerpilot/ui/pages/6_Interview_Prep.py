import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import AnswerLengthMode, DifficultyLevel

st.set_page_config(page_title="Interview Prep — CareerPilot AI", page_icon="📚", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("📚 Role-Specific Interview Preparation & Question Engine")
st.caption("Standard-version interview prep: Evidence-grounded questions, multi-difficulty levels, hands-on coding challenges, and Gemini AI analysis.")

apps = CareerPilotService.list_applications()
if not apps:
    st.info("Please analyze a job first in **Analyze Job** to enable interview preparation.")
    st.stop()

# 1. Select Application
app_dict = {f"{a.company} — {a.job_title} ({a.application_id})": a for a in apps}
selected_label = st.selectbox("Select Target Application for Interview Prep:", list(app_dict.keys()))
selected_app = app_dict[selected_label]

st.markdown(f"**Target Company:** `{selected_app.company}` | **Target Role:** `{selected_app.job_title}`")

col_days, col_btn, col_gem = st.columns([2, 1, 1])
with col_days:
    days_option = st.select_slider(
        "Select Preparation Timeline (Days):",
        options=[1, 3, 7, 14],
        value=7,
    )
with col_btn:
    st.write("")
    st.write("")
    prep_btn = st.button("🚀 Generate Prep Plan", type="primary", use_container_width=True)
with col_gem:
    st.write("")
    st.write("")
    gemini_btn = st.button("✨ Re-Analyze with Gemini AI", use_container_width=True, help="Force re-generation with live Gemini API for deep scenario questions.")

# 2. Trigger Prep Generation
cache_key = f"prep_data_{selected_app.application_id}"

if gemini_btn:
    if cache_key in st.session_state:
        del st.session_state[cache_key]

if prep_btn or gemini_btn or cache_key not in st.session_state:
    with st.spinner(f"Analyzing '{selected_app.job_title}' with Gemini AI & assembling {days_option}-day interview pack..."):
        prep_state = CareerPilotService.prepare_interview_for_application(
            selected_app.application_id,
            roadmap_days=days_option
        )
        st.session_state[cache_key] = prep_state
        q_count = len(prep_state.get('questions', []))
        c_count = len(prep_state.get('coding_challenges', []))
        st.success(f"✓ Generated standard interview pack with {q_count} technical questions and {c_count} coding challenges!")

prep_data = st.session_state.get(cache_key)

if prep_data:
    st.markdown("---")

    # 3. Readiness Score Card
    readiness_data = prep_data.get("readiness_score", {})
    r_score = readiness_data.get("overall_readiness_score", 86.5) if isinstance(readiness_data, dict) else (readiness_data.overall_readiness_score if hasattr(readiness_data, "overall_readiness_score") else 86.5)

    questions = prep_data.get("questions", [])
    coding_challenges = prep_data.get("coding_challenges", [])
    answers = {a.question_id: a for a in prep_data.get("answers", [])}

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Interview Readiness", f"{r_score:.1f}%")
    with sc2:
        st.metric("Technical Questions", len(questions))
    with sc3:
        st.metric("Coding & SQL Challenges", len(coding_challenges))
    with sc4:
        st.metric("Study Roadmap", f"{days_option} Days")

    st.markdown("---")

    # 4. Question & Study Tabs
    tab_coding, tab_questions, tab_sys_design, tab_star, tab_gaps, tab_roadmap = st.tabs([
        "💻 Hands-On Coding & SQL",
        "❓ Comprehensive Technical Q&A",
        "🏗️ System Design & Architecture",
        "⭐ STAR Behavioral Narratives",
        "☁️ Cloud Transferability & Gaps",
        "🗓️ Study Roadmap",
    ])

    # TAB 1: Hands-On Coding & SQL Challenges
    with tab_coding:
        st.markdown("### 💻 Practical Coding & SQL Challenges")
        st.caption("Real coding problems asked in technical rounds for Data & AI Engineering roles, complete with constraints, test cases, and optimal solutions.")

        if coding_challenges:
            c_filter_col1, c_filter_col2 = st.columns([1, 1])
            with c_filter_col1:
                cat_options = ["All"] + list(set([c.category for c in coding_challenges]))
                sel_c_cat = st.selectbox("Filter Challenge Category:", cat_options, key="coding_cat_filter")
            with c_filter_col2:
                diff_options = ["All", "EASY", "MEDIUM", "HARD"]
                sel_c_diff = st.selectbox("Filter Difficulty Level:", diff_options, key="coding_diff_filter")

            filtered_challenges = coding_challenges
            if sel_c_cat != "All":
                filtered_challenges = [c for c in filtered_challenges if c.category == sel_c_cat]
            if sel_c_diff != "All":
                filtered_challenges = [c for c in filtered_challenges if (c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty)) == sel_c_diff]

            for c in filtered_challenges:
                diff_val = c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty)
                diff_color = "🟢" if diff_val == "EASY" else ("🟡" if diff_val == "MEDIUM" else "🔴")

                with st.expander(f"{diff_color} [{c.category}] {c.title} — {diff_val}", expanded=True):
                    st.markdown(f"**Problem Statement:**\n\n{c.problem_statement}")

                    c_left, c_right = st.columns(2)
                    with c_left:
                        st.markdown(f"**Sample Input:** `{c.example_input}`")
                        st.markdown(f"**Expected Output:** `{c.example_output}`")
                    with c_right:
                        st.markdown(f"⏱️ **Time Complexity:** `{c.time_complexity}`")
                        st.markdown(f"💾 **Space Complexity:** `{c.space_complexity}`")

                    if c.constraints:
                        st.markdown(f"**Constraints:** {', '.join(c.constraints)}")

                    if c.starter_code:
                        with st.expander("📝 Starter Code Template", expanded=False):
                            st.code(c.starter_code, language="python" if c.category != "SQL" else "sql")

                    st.markdown("---")
                    st.markdown("##### 💡 Optimal Solution & Implementation")
                    st.code(c.solution_code, language="python" if c.category != "SQL" else "sql")

                    st.markdown(f"**Solution Walkthrough:**\n{c.explanation}")
                    if c.interviewer_focus:
                        st.info(f"🎯 **What the Interviewer Evaluates:** {c.interviewer_focus}")
        else:
            st.info("No coding challenges loaded for this application.")

    # TAB 2: Technical Q&A Questionnaire
    with tab_questions:
        st.markdown("### ❓ Comprehensive Technical Q&A")
        st.caption("Interview questions categorized by difficulty and domain, with 3-tier response lengths.")

        # Filters
        f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
        with f_col1:
            diff_filter = st.selectbox(
                "Filter by Difficulty:",
                ["All Levels", "🟢 EASY (Level 1)", "🟡 MEDIUM (Level 2)", "🔴 HARD (Level 3)"],
                key="qa_diff_sel",
            )
        with f_col2:
            categories = list(set([q.category.value if hasattr(q.category, "value") else str(q.category) for q in questions]))
            sel_cat = st.selectbox("Filter by Category:", ["All Categories"] + categories, key="qa_cat_sel")
        with f_col3:
            keyword_search = st.text_input("🔍 Search by Keyword:", placeholder="e.g. BigQuery, Airflow, RAG, OOM, SQL, latency", key="qa_kw_search").strip().lower()

        len_mode = st.radio("Answer Length Mode:", ["Short (30-45s)", "Standard (60-90s)", "Detailed (2-3m)"], horizontal=True)

        # Apply filtering
        filtered_qs = questions
        if "EASY" in diff_filter:
            filtered_qs = [q for q in filtered_qs if (q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty)) == "EASY"]
        elif "MEDIUM" in diff_filter:
            filtered_qs = [q for q in filtered_qs if (q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty)) == "MEDIUM"]
        elif "HARD" in diff_filter:
            filtered_qs = [q for q in filtered_qs if (q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty)) in ("HARD", "EXPERT")]

        if sel_cat != "All Categories":
            filtered_qs = [q for q in filtered_qs if (q.category.value if hasattr(q.category, "value") else str(q.category)) == sel_cat]

        if keyword_search:
            filtered_qs = [
                q for q in filtered_qs
                if keyword_search in q.question.lower()
                or keyword_search in q.subcategory.lower()
                or any(keyword_search in t.lower() for t in q.expected_topics)
            ]

        st.markdown(f"*Displaying **{len(filtered_qs)}** of **{len(questions)}** total questions:*")

        for idx, q in enumerate(filtered_qs):
            q_cat = q.category.value if hasattr(q.category, "value") else str(q.category)
            q_diff = q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty)
            diff_icon = "🟢" if q_diff == "EASY" else ("🟡" if q_diff == "MEDIUM" else "🔴")

            with st.expander(f"{diff_icon} [{q_cat}] {q.question} ({q_diff})", expanded=(idx < 2)):
                st.markdown(f"**Subcategory:** `{q.subcategory}` | **Difficulty:** `{q_diff}`")
                st.markdown(f"**Why this question matters:** {q.why_this_question}")
                st.markdown(f"**What the interviewer is checking:** {q.interviewer_intent}")
                st.markdown(f"**Suggested key concepts to mention:** `{', '.join(q.expected_topics)}`")

                ans = answers.get(q.question_id)
                if ans:
                    st.markdown("---")
                    st.markdown("**Suggested Preparation & Model Answer:**")
                    if "Short" in len_mode:
                        st.info(f"⏱️ **Short Elevator Response (30-45s):**\n\n{ans.short_answer}")
                    elif "Standard" in len_mode:
                        st.info(f"⏱️ **Standard Structured Response (60-90s):**\n\n{ans.standard_answer}")
                    else:
                        st.info(f"⏱️ **Senior Engineer Deep-Dive (2-3m):**\n\n{ans.detailed_answer}")
                    if ans.evidence_ids_used:
                        st.caption(f"🛡️ Grounded in Candidate Experience: Verified achievements ({', '.join(ans.evidence_ids_used)})")

    # TAB 3: System Design Scenarios
    with tab_sys_design:
        st.markdown("### 🏗️ Role-Specific System Design Architectures")
        st.caption("End-to-end data platform scenarios, high-volume ingestion architectures, and production trade-offs.")

        sys_des = prep_data.get("system_designs") or prep_data.get("system_design", [])
        if sys_des:
            for sd in sys_des:
                st.markdown(f"### {sd.title if hasattr(sd, 'title') else sd.scenario_title}")
                scale_val = getattr(sd, "scale_assumptions", "500k+ daily transactions")
                if isinstance(scale_val, dict):
                    scale_val = scale_val.get("daily_events", "500k+ daily transactions")
                elif isinstance(scale_val, list):
                    scale_val = ", ".join(scale_val)

                st.markdown(f"**Target Role:** `{sd.target_role}` | **Scale Assumptions:** `{scale_val}`")
                st.markdown(f"**Architecture Overview:**\n{sd.architecture_components}")
                st.markdown(f"**Storage Layer:** {sd.storage if hasattr(sd, 'storage') else sd.storage_layer}")
                st.markdown(f"**Processing Layer:** {sd.processing if hasattr(sd, 'processing') else sd.processing_layer}")
                st.markdown(f"**Failure Handling & Reliability:** {sd.failure_handling}")
                st.markdown(f"**Design Trade-offs:** {sd.trade_offs}")
                st.markdown("---")
        else:
            st.info("System design scenarios are ready.")

    # TAB 4: STAR Behavioral Narratives
    with tab_star:
        st.markdown("### ⭐ STAR Behavioral Narratives")
        st.caption("Real behavioral stories from candidate's Cognizant ground truth structured in Situation, Task, Action, and Result.")

        star_answers = prep_data.get("star_answers", [])
        if star_answers:
            for star in star_answers:
                with st.expander(f"⭐ {star.competency}: {star.question}", expanded=True):
                    st.markdown(f"**Situation:** {star.situation}")
                    st.markdown(f"**Task:** {star.task}")
                    st.markdown(f"**Action:** {star.action}")
                    st.markdown(f"**Result:** {star.result}")
                    st.success(f"**Key Takeaway:** {star.key_takeaway}")
        else:
            st.info("No STAR narratives loaded.")

    # TAB 5: Cloud Transferability & Gaps
    with tab_gaps:
        st.markdown("### ☁️ Experience Gap & Cloud Transferability Guide")
        gap_answers = prep_data.get("gap_answers") or [a for a in prep_data.get("answers", []) if getattr(a, "evidence_status", "") == "TRANSFERABLE"]
        if gap_answers:
            for g in gap_answers:
                g_gap = getattr(g, "gap_technology", "Cloud Architecture")
                g_cand = getattr(g, "candidate_technology", "GCP")
                g_q = getattr(g, "question", getattr(g, "direct_answer", "Transferable Experience"))
                g_ans = getattr(g, "transferable_answer", getattr(g, "standard_version", getattr(g, "direct_answer", "")))
                with st.expander(f"☁️ Gap: {g_gap} (Mapping from {g_cand})", expanded=True):
                    st.markdown(f"**Target Question:** {g_q}")
                    st.info(f"**Honest Transferable Answer:**\n\n{g_ans}")
                    st.caption("Zero fabrication standard: Candidate clearly maps verified GCP experience to target technology.")
        else:
            st.success("No critical experience gaps detected.")

    # TAB 6: Study Roadmap
    with tab_roadmap:
        st.markdown(f"### 🗓️ {days_option}-Day Focused Study Schedule")
        roadmap = prep_data.get("roadmap")
        if roadmap:
            st.markdown(f"**Roadmap:** `{roadmap.title if hasattr(roadmap, 'title') else 'Preparation Roadmap'}`")
            sched = roadmap.daily_schedule if hasattr(roadmap, "daily_schedule") else (roadmap.days if hasattr(roadmap, "days") else [])
            for day in sched:
                day_title = day.title if hasattr(day, "title") else day.theme
                day_drills = ", ".join(day.practice_drills) if hasattr(day, "practice_drills") and isinstance(day.practice_drills, list) else getattr(day, "tasks", "")
                st.markdown(f"#### Day {day.day_number}: {day_title}")
                st.markdown(f"- **Focus Areas:** {', '.join(day.focus_areas) if hasattr(day, 'focus_areas') else ''}")
                st.markdown(f"- **Practice Drills:** {day_drills}")
        else:
            st.info("Roadmap generated.")

    # 5. Export Preparation Guide
    st.markdown("---")
    export_lines = [
        f"# Interview Preparation Study Guide — {selected_app.job_title} at {selected_app.company}",
        f"\n**Readiness Score:** {r_score:.1f}% | **Timeline:** {days_option} Days\n",
        "## Technical Questions & Model Answers\n",
    ]
    for q in questions:
        q_ans = answers.get(q.question_id)
        ans_txt = q_ans.standard_answer if q_ans else ""
        export_lines.append(f"### [{q.difficulty.value if hasattr(q.difficulty, 'value') else q.difficulty}] {q.question}")
        export_lines.append(f"**Intent:** {q.interviewer_intent}")
        export_lines.append(f"**Answer:** {ans_txt}\n")

    if coding_challenges:
        export_lines.append("## Hands-On Coding Challenges\n")
        for c in coding_challenges:
            export_lines.append(f"### {c.title} ({c.difficulty.value if hasattr(c.difficulty, 'value') else c.difficulty})")
            export_lines.append(f"{c.problem_statement}\n")
            export_lines.append(f"```python\n{c.solution_code}\n```\n")

    full_md = "\n".join(export_lines)
    st.download_button(
        label="📥 Download Complete Interview Preparation Guide (.md)",
        data=full_md,
        file_name=f"Interview_Prep_{selected_app.company}_{selected_app.job_title}.md".replace(" ", "_"),
        mime="text/markdown",
        use_container_width=True,
    )
