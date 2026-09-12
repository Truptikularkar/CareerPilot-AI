import sys
from pathlib import Path

# Ensure root directory is in sys.path for Streamlit Cloud deployment
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import pandas as pd
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
)

st.set_page_config(page_title="Mock Interview — CareerPilot AI", page_icon="🎙️", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("🎙️ Adaptive Mock Interview Agent")
st.caption("Interactive, multi-turn mock interviews with real-time 10-dimensional evaluation, Truth Guard auditing, and dynamic follow-up probing.")

apps = CareerPilotService.list_applications()
if not apps:
    st.info("Please analyze a job description in **Analyze Job** to enable mock interviews.")
    st.stop()

# 1. Session Setup
if "mock_session_state" not in st.session_state:
    st.session_state.mock_session_state = None
if "mock_history" not in st.session_state:
    st.session_state.mock_history = []
if "mock_finished" not in st.session_state:
    st.session_state.mock_finished = False

if not st.session_state.mock_session_state:
    st.subheader("⚙️ Mock Interview Configuration")
    
    col_a, col_b = st.columns(2)
    with col_a:
        app_dict = {f"{a.company} — {a.job_title} ({a.application_id})": a for a in apps}
        selected_app_label = st.selectbox("Target Application:", list(app_dict.keys()))
        target_app = app_dict[selected_app_label]
        
        mode_str = st.selectbox("Interview Mode:", [m.value for m in MockInterviewMode], index=0)
        diff_str = st.selectbox("Difficulty Adaptation:", [d.value for d in InterviewDifficulty], index=4)  # Default ADAPTIVE
        
    with col_b:
        persona_str = st.selectbox("Interviewer Persona:", [p.value for p in InterviewerPersona], index=0)
        feedback_str = st.selectbox("Feedback Mode:", [FeedbackMode.COACHING_MODE.value, FeedbackMode.INTERVIEW_MODE.value], index=0)
        q_count = st.slider("Total Questions Planned:", min_value=2, max_value=12, value=4)

    if st.button("🚀 Start Mock Interview Session", type="primary", use_container_width=True):
        with st.spinner("Initializing adaptive mock interview agent and loading question pool..."):
            session_state = CareerPilotService.start_mock_interview_for_application(
                app_id=target_app.application_id,
                mode=MockInterviewMode(mode_str),
                difficulty=InterviewDifficulty(diff_str),
                persona=InterviewerPersona(persona_str),
                feedback_mode=FeedbackMode(feedback_str),
                total_questions=q_count,
            )
            st.session_state.mock_session_state = session_state
            st.session_state.mock_history = []
            st.session_state.mock_finished = False
            st.session_state.current_hint = HintMode.NO_HINT
            st.success("Mock Interview Started!")
            st.rerun()

else:
    # Active Mock Session
    state = st.session_state.mock_session_state
    session_id = state["session_id"]
    turns = state["turns"]
    curr_turn = turns[-1]
    
    st.markdown(f"**Session ID:** `{session_id}` | **Role:** `{state['role']}` | **Persona:** `{state['persona'].value}` | **Mode:** `{state['mode'].value}`")
    st.progress(len(turns) / state["total_questions_planned"], text=f"Question {curr_turn.turn_number} of {state['total_questions_planned']}")

    if not st.session_state.mock_finished:
        st.markdown("---")
        
        # Interviewer Prompt Card
        depth_badge = f" `(Follow-up Depth: Level {curr_turn.followup_depth})`" if curr_turn.followup_depth > 0 else ""
        st.markdown(f"### 🤖 [{state['persona'].value}] Turn {curr_turn.turn_number}{depth_badge}")
        st.markdown(f"**Topic:** `{curr_turn.topic}` | **Difficulty:** `{curr_turn.difficulty}`")
        st.info(f"### \"{curr_turn.question_text}\"")

        # Candidate Answer Input
        answer_input = st.text_area("Your Answer:", height=140, key=f"turn_ans_{curr_turn.turn_number}", placeholder="Structure your response with clear engineering logic, concrete metrics, and trade-offs...")

        # Hint & Action Buttons
        h_col1, h_col2, h_col3, h_col4 = st.columns([1, 1, 1, 2])
        hint_to_use = HintMode.NO_HINT
        
        with h_col1:
            if st.button("💡 Small Hint (-5%)"):
                st.warning("💡 **Small Hint:** Focus on the underlying architectural mechanism, data flow, and failure handling.")
                hint_to_use = HintMode.SMALL_HINT
        with h_col2:
            if st.button("💡 Full Hint (-15%)"):
                st.warning(f"💡 **Full Hint:** Core keywords: {', '.join(curr_turn.topic.split()[:2])}, trade-offs, and measurable outcome.")
                hint_to_use = HintMode.FULL_HINT
        with h_col3:
            if st.button("🤷 I Don't Know"):
                answer_input = "I don't know the exact internal implementation details of this concept."

        with h_col4:
            submit_btn = st.button("💬 Submit Answer & Continue", type="primary", use_container_width=True)

        if submit_btn:
            if not answer_input.strip():
                st.error("Please enter an answer or select 'I Don't Know'.")
            else:
                with st.spinner("Evaluating answer across 10 dimensions & auditing truth..."):
                    evaluation = CareerPilotService.submit_mock_answer(
                        session_id=session_id,
                        answer_text=answer_input.strip(),
                        hint_used=hint_to_use,
                    )
                    st.session_state.mock_history.append((curr_turn, answer_input, evaluation))

                    # Check for Next Turn or Finish
                    next_turn, is_finished = CareerPilotService.continue_mock_session(session_id)
                    if is_finished or not next_turn:
                        st.session_state.mock_finished = True
                    st.rerun()

        # Instant Coaching Display for last turn if in Coaching Mode
        if state["feedback_mode"] == FeedbackMode.COACHING_MODE and st.session_state.mock_history:
            last_turn, last_ans, last_eval = st.session_state.mock_history[-1]
            st.markdown("---")
            st.subheader("🎯 Real-Time Coaching Feedback (Turn Just Completed)")
            
            fb_col1, fb_col2 = st.columns([1, 2])
            with fb_col1:
                st.metric("Turn Score", f"{last_eval.overall_turn_score:.1f}%")
            with fb_col2:
                if last_eval.correct_concepts:
                    st.success(f"✓ **Strong Concepts:** {', '.join(last_eval.correct_concepts[:3])}")
                if last_eval.missing_concepts:
                    st.warning(f"⚠ **Missing Concepts:** {', '.join(last_eval.missing_concepts[:2])}")
                if last_eval.truth_checks:
                    for tc in last_eval.truth_checks:
                        st.error(f"🚨 **Truth Warning:** {tc.explanation}")
                st.info(f"💡 **Coaching Tip:** {last_eval.coaching_tip}")

        st.markdown("---")
        if st.button("⏹️ Finish Interview Early & View Final Report"):
            st.session_state.mock_finished = True
            st.rerun()

    else:
        # Final Report Screen
        st.markdown("---")
        st.header("🏆 Mock Interview Final Performance Report")
        with st.spinner("Compiling multi-dimensional scores and topic mastery..."):
            report = CareerPilotService.finish_mock_interview(session_id)

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Overall Score", f"{report.overall_score:.1f}%")
        with sc2:
            st.metric("Technical Depth", f"{report.technical_score:.1f}%")
        with sc3:
            st.metric("Communication", f"{report.communication_score:.1f}%")
        with sc4:
            st.metric("Truth Guard Accuracy", f"{report.experience_accuracy_score:.1f}%")

        st.markdown(f"> **Executive Summary:** {report.executive_summary}")
        st.markdown("---")

        # Sub-score Tabs
        tab_scores, tab_mastery, tab_weak, tab_transcript = st.tabs([
            "📊 Dimension Scores",
            "🧠 Topic Mastery",
            "⚠️ Weaknesses & Recommendations",
            "📜 Full Transcript",
        ])

        with tab_scores:
            s_rows = [
                {"Dimension": "Technical Correctness & Depth", "Score": f"{report.technical_score:.1f}%"},
                {"Dimension": "Communication, Clarity & Structure", "Score": f"{report.communication_score:.1f}%"},
                {"Dimension": "Resume Knowledge & Evidence Grounding", "Score": f"{report.resume_knowledge_score:.1f}%"},
                {"Dimension": "Project Depth & Ownership", "Score": f"{report.project_score:.1f}%"},
                {"Dimension": "System Design & Architecture", "Score": f"{report.system_design_score:.1f}%"},
                {"Dimension": "Behavioral STAR Storytelling", "Score": f"{report.behavioral_score:.1f}%"},
                {"Dimension": "Problem Solving & Follow-ups", "Score": f"{report.problem_solving_score:.1f}%"},
                {"Dimension": "Experience Accuracy & Truth Guard", "Score": f"{report.experience_accuracy_score:.1f}%"},
            ]
            st.dataframe(pd.DataFrame(s_rows), use_container_width=True, hide_index=True)

        with tab_mastery:
            st.markdown("### Topic Mastery Breakdown")
            m_rows = []
            for top, m in report.topic_mastery.items():
                m_rows.append({
                    "Topic": top,
                    "Mastery Score (0-5)": f"{m.mastery_score:.1f} / 5.0",
                    "Questions Asked": m.questions_asked,
                    "Status": m.status,
                })
            st.dataframe(pd.DataFrame(m_rows), use_container_width=True, hide_index=True)

        with tab_weak:
            st.markdown("### Candidate Strengths")
            for s in report.strengths:
                st.success(f"✓ **{s.topic}:** {s.description}")

            st.markdown("### Areas for Improvement")
            for w in report.weaknesses:
                st.warning(f"⚠ **{w.topic}:** {w.description}\n\n*Suggested Remedy: {w.suggested_remedy}*")

            st.markdown("### Recommended Study Topics")
            for idx, r in enumerate(report.recommended_study_topics, 1):
                st.info(f"**{idx}.** {r}")

        with tab_transcript:
            st.markdown("### Turn-by-Turn Interview Transcript")
            for t, ans, ev in st.session_state.mock_history:
                st.markdown(f"#### Turn {t.turn_number}: [{t.topic}] {t.question_text}")
                st.markdown(f"**Candidate Answer:**\n> {ans}")
                st.markdown(f"**Turn Score:** `{ev.overall_turn_score:.1f}%` | **Feedback:** {ev.feedback}")
                st.markdown("---")

        if st.button("🔄 Start New Mock Interview Session"):
            st.session_state.mock_session_state = None
            st.session_state.mock_history = []
            st.session_state.mock_finished = False
            st.rerun()
