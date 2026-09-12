import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
    SessionStatus,
)
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.mock_interview import (
    MockInterviewTurn,
    AnswerEvaluation,
    FinalInterviewReport,
    TopicMastery,
    WeaknessItem,
    StrengthItem,
)
from careerpilot.graphs.state import MockInterviewState
from careerpilot.interview.question_planner import QuestionPlanner
from careerpilot.interview.question_engine import QuestionEngine
from careerpilot.interview.gap_handler import GapHandler
from careerpilot.interview.star_engine import STAREngine
from careerpilot.interview.mock_question_selector import MockQuestionSelector
from careerpilot.interview.answer_evaluator import AnswerEvaluator
from careerpilot.interview.weakness_analyzer import WeaknessAnalyzer
from careerpilot.interview.interview_scorer import InterviewScorer
from careerpilot.interview.session_store import SessionStore
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class MockInterviewService:
    """
    Stateful service layer orchestrating interactive mock interview sessions,
    providing clean API endpoints for CLI, tests, and future Streamlit UI.
    """

    _active_sessions: Dict[str, MockInterviewState] = {}

    @classmethod
    def start_session(
        cls,
        job_input: Union[str, Path],
        mode: MockInterviewMode = MockInterviewMode.FULL_INTERVIEW,
        difficulty: InterviewDifficulty = InterviewDifficulty.ADAPTIVE,
        persona: InterviewerPersona = InterviewerPersona.SENIOR_ENGINEER,
        feedback_mode: FeedbackMode = FeedbackMode.INTERVIEW_MODE,
        total_questions: int = 8,
    ) -> MockInterviewState:
        from careerpilot.graphs.job_analysis_graph import analyze_job
        from careerpilot.graphs.resume_graph import generate_tailored_resume
        from careerpilot.ats.evaluator import ATSEvaluator

        session_id = f"session_{uuid.uuid4().hex[:8]}"


        # 1. Resolve Analysis, Resume & Readiness Seed
        analysis = analyze_job(job_input)
        resume = generate_tailored_resume(analysis)
        ats_rep = ATSEvaluator.evaluate_resume(resume, analysis)
        seed = ats_rep.interview_seed

        # 2. Generate Question Pool
        quotas = QuestionPlanner.plan_question_distribution(analysis, seed, resume)
        core_qs = QuestionEngine.generate_interview_questions(analysis, resume, seed, quotas)
        star_qs, _ = STAREngine.generate_star_questions_and_answers()
        gap_qs, _ = GapHandler.generate_gap_questions_and_answers(analysis, seed)
        all_qs = core_qs + star_qs + gap_qs

        # 3. Create Session in DB
        SessionStore.create_session(
            session_id=session_id,
            job_id=analysis.job_id,
            target_role=resume.strategy.target_role,
            mode=mode,
            difficulty=difficulty,
            persona=persona,
        )

        # 4. Select Initial Question
        first_q, depth = MockQuestionSelector.select_next_question(
            available_questions=all_qs,
            previous_turns=[],
            mode=mode,
            difficulty=difficulty,
            persona=persona,
            weakness_topics=[],
            total_questions_planned=total_questions,
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

        state: MockInterviewState = {
            "session_id": session_id,
            "job_id": analysis.job_id,
            "role": resume.strategy.target_role,
            "strategy": resume.strategy.strategy_type.value,
            "mode": mode,
            "difficulty": difficulty,
            "persona": persona,
            "feedback_mode": feedback_mode,
            "hint_mode": HintMode.NO_HINT,
            "job_analysis": analysis,
            "tailored_resume": resume,
            "readiness_seed": seed,
            "all_available_questions": all_qs,
            "total_questions_planned": total_questions,
            "questions_asked": 1,
            "questions_remaining": max(0, total_questions - 1),
            "current_turn_number": 1,
            "current_question": first_q,
            "current_question_text": first_q.question,
            "current_question_type": first_q.category.value,
            "current_topic": first_q.subcategory,
            "current_difficulty": first_q.difficulty.value,
            "followup_depth": depth,
            "current_answer": "",
            "current_hint": HintMode.NO_HINT,
            "current_evaluation": None,
            "turns": [first_turn],
            "question_history": [first_q.question],
            "answer_history": [],
            "evaluation_history": [],
            "topic_scores": {},
            "skill_scores": {},
            "weakness_topics": [],
            "strength_topics": [],
            "jd_coverage": {},
            "candidate_confidence": 1.0,
            "session_status": SessionStatus.IN_PROGRESS,
            "final_score": None,
            "final_report": None,
        }

        cls._active_sessions[session_id] = state
        SessionStore.save_turn(session_id, first_turn)
        logger.info("Initialized mock interview session '%s' with %d planned questions.", session_id, total_questions)
        return state

    @classmethod
    def get_session_state(cls, session_id: str) -> Optional[MockInterviewState]:
        return cls._active_sessions.get(session_id)

    @classmethod
    def submit_answer(
        cls,
        session_id: str,
        candidate_answer: str,
        hint_used: HintMode = HintMode.NO_HINT,
    ) -> AnswerEvaluation:
        state = cls._active_sessions.get(session_id)
        if not state:
            raise ValueError(f"Active session '{session_id}' not found.")

        current_q = state["current_question"]
        current_turn = state["turns"][-1]

        # 1. Evaluate Answer
        evaluation = AnswerEvaluator.evaluate_answer(
            question=current_q,
            candidate_answer=candidate_answer,
            hint_used=hint_used,
            target_role=state["role"],
            followup_depth=current_turn.followup_depth,
        )

        # 2. Update Turn Record
        current_turn.candidate_answer = candidate_answer
        current_turn.hint_used = hint_used
        current_turn.evaluation = evaluation

        # 3. Update State History
        state["current_answer"] = candidate_answer
        state["current_evaluation"] = evaluation
        state["answer_history"].append(candidate_answer)
        state["evaluation_history"].append(evaluation)

        # Update topic score tracking
        top = current_turn.topic or current_turn.category
        state["topic_scores"][top] = evaluation.overall_turn_score

        # Save to DB
        SessionStore.save_turn(session_id, current_turn)
        return evaluation

    @classmethod
    def continue_session(
        cls,
        session_id: str,
    ) -> Tuple[Optional[MockInterviewTurn], bool]:
        state = cls._active_sessions.get(session_id)
        if not state:
            raise ValueError(f"Active session '{session_id}' not found.")

        # Check if reached planned limit or candidate chose to finish
        if len(state["turns"]) >= state["total_questions_planned"]:
            cls.finish_session(session_id)
            return None, True

        # Extract current weaknesses
        weaknesses, _, _ = WeaknessAnalyzer.analyze_session(state["turns"])
        weak_topics = [w.topic for w in weaknesses]
        state["weakness_topics"] = weak_topics

        # Select next question adaptively
        next_q, depth = MockQuestionSelector.select_next_question(
            available_questions=state["all_available_questions"],
            previous_turns=state["turns"],
            mode=state["mode"],
            difficulty=state["difficulty"],
            persona=state["persona"],
            weakness_topics=weak_topics,
            total_questions_planned=state["total_questions_planned"],
        )

        turn_num = len(state["turns"]) + 1
        new_turn = MockInterviewTurn(
            turn_id=f"turn_{uuid.uuid4().hex[:8]}",
            turn_number=turn_num,
            question_id=next_q.question_id,
            question_text=next_q.question,
            category=next_q.category.value,
            topic=next_q.subcategory,
            difficulty=next_q.difficulty.value,
            followup_depth=depth,
            candidate_answer="",
            hint_used=HintMode.NO_HINT,
            evaluation=None,
        )

        state["turns"].append(new_turn)
        state["questions_asked"] = turn_num
        state["questions_remaining"] = max(0, state["total_questions_planned"] - turn_num)
        state["current_turn_number"] = turn_num
        state["current_question"] = next_q
        state["current_question_text"] = next_q.question
        state["current_question_type"] = next_q.category.value
        state["current_topic"] = next_q.subcategory
        state["current_difficulty"] = next_q.difficulty.value
        state["followup_depth"] = depth
        state["current_answer"] = ""
        state["current_evaluation"] = None
        state["question_history"].append(next_q.question)

        SessionStore.save_turn(session_id, new_turn)
        return new_turn, False

    @classmethod
    def finish_session(cls, session_id: str) -> FinalInterviewReport:
        state = cls._active_sessions.get(session_id)
        if not state:
            # Try to load from SessionStore if already closed in memory
            db_data = SessionStore.get_session(session_id)
            if not db_data:
                raise ValueError(f"Session '{session_id}' not found.")
            # Construct report from persisted turns
            turns = [MockInterviewTurn(**t) for t in db_data.get("turns", [])]
            scores, topic_mastery, jd_cov, chal, well, poorly, truth_c = InterviewScorer.score_session(
                turns=turns,
                job_analysis=None,
            )
            weaknesses, strengths, recs = WeaknessAnalyzer.analyze_session(turns)
            return FinalInterviewReport(
                session_id=session_id,
                job_id=db_data.get("job_id", ""),
                target_role=db_data.get("target_role", "AI Data Engineer"),
                mode=MockInterviewMode.FULL_INTERVIEW,
                persona=InterviewerPersona.SENIOR_ENGINEER,
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
                jd_coverage=[],
                challenging_questions=chal,
                questions_answered_well=well,
                questions_answered_poorly=poorly,
                unsupported_claims=truth_c,
                recommended_study_topics=recs,
                recommended_next_mock_mode=MockInterviewMode.WEAKNESS_FOCUS if weaknesses else MockInterviewMode.FULL_INTERVIEW,
                executive_summary=f"Mock interview completed across {len(turns)} turns with overall score of {scores['overall_score']}%.",
            )

        # Compute deterministic scores
        scores, topic_mastery, jd_cov, chal, well, poorly, truth_c = InterviewScorer.score_session(
            turns=state["turns"],
            job_analysis=state["job_analysis"],
        )

        # Analyze strengths, weaknesses and study roadmap
        weaknesses, strengths, recs = WeaknessAnalyzer.analyze_session(state["turns"])

        next_mode = MockInterviewMode.WEAKNESS_FOCUS if weaknesses else MockInterviewMode.FULL_INTERVIEW

        report = FinalInterviewReport(
            session_id=session_id,
            job_id=state["job_id"],
            target_role=state["role"],
            mode=state["mode"],
            persona=state["persona"],
            total_turns=len(state["turns"]),
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
            executive_summary=f"Completed {state['mode'].value} mock interview with overall score of {scores['overall_score']}%. Candidate demonstrated strong grasp of core data pipelines with targeted opportunities in deeper failure recovery and cloud transferability.",
        )

        state["session_status"] = SessionStatus.COMPLETED
        state["final_score"] = scores["overall_score"]
        state["final_report"] = report

        # Persist completion and export artifacts
        SessionStore.complete_session(session_id, report)
        SessionStore.export_session_artifacts(session_id, state["turns"], report)

        return report
