import uuid
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
    SessionStatus,
)
from careerpilot.graphs.state import MockInterviewState
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.interview.question_planner import QuestionPlanner
from careerpilot.interview.question_engine import QuestionEngine
from careerpilot.interview.gap_handler import GapHandler
from careerpilot.interview.star_engine import STAREngine
from careerpilot.interview.mock_question_selector import MockQuestionSelector
from careerpilot.interview.answer_evaluator import AnswerEvaluator
from careerpilot.interview.weakness_analyzer import WeaknessAnalyzer
from careerpilot.interview.interview_scorer import InterviewScorer
from careerpilot.interview.session_store import SessionStore
from careerpilot.models.mock_interview import MockInterviewTurn, FinalInterviewReport
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


def init_session_node(state: MockInterviewState) -> Dict[str, Any]:
    logger.info("LangGraph Mock Node: Initializing session state...")
    job_input = state.get("job_input", "data/jobs/evaluation/01_ai_data_engineer.txt")
    mode = state.get("mode", MockInterviewMode.FULL_INTERVIEW)
    diff = state.get("difficulty", InterviewDifficulty.ADAPTIVE)
    persona = state.get("persona", InterviewerPersona.SENIOR_ENGINEER)
    total_q = state.get("total_questions_planned", 8)

    session_id = state.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"

    analysis = analyze_job(job_input)
    resume = generate_tailored_resume(analysis)
    ats_rep = ATSEvaluator.evaluate_resume(resume, analysis)
    seed = ats_rep.interview_seed

    quotas = QuestionPlanner.plan_question_distribution(analysis, seed, resume)
    core_qs = QuestionEngine.generate_interview_questions(analysis, resume, seed, quotas)
    star_qs, _ = STAREngine.generate_star_questions_and_answers()
    gap_qs, _ = GapHandler.generate_gap_questions_and_answers(analysis, seed)
    all_qs = core_qs + star_qs + gap_qs

    SessionStore.create_session(
        session_id=session_id,
        job_id=analysis.job_id,
        target_role=resume.strategy.target_role,
        mode=mode,
        difficulty=diff,
        persona=persona,
    )

    first_q, depth = MockQuestionSelector.select_next_question(
        available_questions=all_qs,
        previous_turns=[],
        mode=mode,
        difficulty=diff,
        persona=persona,
        weakness_topics=[],
        total_questions_planned=total_q,
    )

    first_turn = MockInterviewTurn(
        turn_id=f"turn_{uuid.uuid4().hex[:8]}",
        turn_number=1,
        question_id=first_q.question_id,
        question_text=first_q.question,
        category=first_q.category.value,
        topic=first_q.subcategory,
        difficulty=first_q.difficulty.value,
        followup_depth=depth,
        candidate_answer="",
        hint_used=HintMode.NO_HINT,
        evaluation=None,
    )

    SessionStore.save_turn(session_id, first_turn)

    return {
        "session_id": session_id,
        "job_id": analysis.job_id,
        "role": resume.strategy.target_role,
        "strategy": resume.strategy.strategy_type.value,
        "mode": mode,
        "difficulty": diff,
        "persona": persona,
        "job_analysis": analysis,
        "tailored_resume": resume,
        "readiness_seed": seed,
        "all_available_questions": all_qs,
        "total_questions_planned": total_q,
        "questions_asked": 1,
        "questions_remaining": max(0, total_q - 1),
        "current_turn_number": 1,
        "current_question": first_q,
        "current_question_text": first_q.question,
        "current_question_type": first_q.category.value,
        "current_topic": first_q.subcategory,
        "current_difficulty": first_q.difficulty.value,
        "followup_depth": depth,
        "turns": [first_turn],
        "question_history": [first_q.question],
        "answer_history": [],
        "evaluation_history": [],
        "topic_scores": {},
        "skill_scores": {},
        "weakness_topics": [],
        "strength_topics": [],
        "session_status": SessionStatus.IN_PROGRESS,
    }


def evaluate_turn_node(state: MockInterviewState) -> Dict[str, Any]:
    logger.info("LangGraph Mock Node: Evaluating candidate answer...")
    current_q = state["current_question"]
    candidate_answer = state.get("current_answer", "")
    hint_used = state.get("current_hint", HintMode.NO_HINT)
    depth = state.get("followup_depth", 0)

    evaluation = AnswerEvaluator.evaluate_answer(
        question=current_q,
        candidate_answer=candidate_answer,
        hint_used=hint_used,
        target_role=state.get("role", "AI Data Engineer"),
        followup_depth=depth,
    )

    turns = state["turns"]
    if turns:
        turns[-1].candidate_answer = candidate_answer
        turns[-1].hint_used = hint_used
        turns[-1].evaluation = evaluation
        SessionStore.save_turn(state["session_id"], turns[-1])

    eval_hist = state.get("evaluation_history", []) + [evaluation]
    ans_hist = state.get("answer_history", []) + [candidate_answer]

    top = state.get("current_topic", "General")
    topic_scores = dict(state.get("topic_scores", {}))
    topic_scores[top] = evaluation.overall_turn_score

    return {
        "current_evaluation": evaluation,
        "turns": turns,
        "evaluation_history": eval_hist,
        "answer_history": ans_hist,
        "topic_scores": topic_scores,
    }


def finalize_session_node(state: MockInterviewState) -> Dict[str, Any]:
    logger.info("LangGraph Mock Node: Finalizing mock interview session and generating report...")
    session_id = state["session_id"]
    turns = state["turns"]
    job_analysis = state["job_analysis"]

    scores, topic_mastery, jd_cov, chal, well, poorly, truth_c = InterviewScorer.score_session(
        turns=turns,
        job_analysis=job_analysis,
    )
    weaknesses, strengths, recs = WeaknessAnalyzer.analyze_session(turns)
    next_mode = MockInterviewMode.WEAKNESS_FOCUS if weaknesses else MockInterviewMode.FULL_INTERVIEW

    report = FinalInterviewReport(
        session_id=session_id,
        job_id=state["job_id"],
        target_role=state["role"],
        mode=state["mode"],
        persona=state["persona"],
        total_turns=len(turns),
        overall_score=scores["overall_score"],
        technical_score=scores["technical_score"],
        communication_score=scores["communication_score"],
        resume_knowledge_score=scores["resume_knowledge_score"],
        project_score=scores["project_score"],
        system_design_score=scores["system_design_score"],
        behavioral_score=scores["behavioral_score"],
        problem_solving_score=scores["problem_solving_score"],
        experience_accuracy_score=scores["experience_accuracy_score"],
        topic_mastery=topic_mastery,
        strengths=strengths,
        weaknesses=weaknesses,
        jd_coverage=jd_cov,
        challenging_questions=chal,
        questions_answered_well=well,
        questions_answered_poorly=poorly,
        unsupported_claims=truth_c,
        recommended_study_topics=recs,
        recommended_next_mock_mode=next_mode,
        executive_summary=f"Completed {state['mode'].value} mock interview with overall score of {scores['overall_score']}%.",
    )

    SessionStore.complete_session(session_id, report)
    SessionStore.export_session_artifacts(session_id, turns, report)

    return {
        "final_report": report,
        "final_score": scores["overall_score"],
        "session_status": SessionStatus.COMPLETED,
    }


# -----------------------------------------------------------------------------
# Graph Construction & Compilation
# -----------------------------------------------------------------------------
builder = StateGraph(MockInterviewState)

builder.add_node("init_session", init_session_node)
builder.add_node("evaluate_turn", evaluate_turn_node)
builder.add_node("finalize_session", finalize_session_node)

builder.add_edge(START, "init_session")
builder.add_edge("init_session", END)
builder.add_edge("evaluate_turn", "finalize_session")
builder.add_edge("finalize_session", END)

mock_interview_graph = builder.compile()
