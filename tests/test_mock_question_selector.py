import pytest
from pathlib import Path
from careerpilot.core.constants import MockInterviewMode, InterviewDifficulty, InterviewerPersona, QuestionCategory
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.interview.question_planner import QuestionPlanner
from careerpilot.interview.question_engine import QuestionEngine
from careerpilot.interview.gap_handler import GapHandler
from careerpilot.interview.star_engine import STAREngine
from careerpilot.interview.mock_question_selector import MockQuestionSelector


@pytest.fixture
def question_pool():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)
    ats_rep = ATSEvaluator.evaluate_resume(resume, analysis)
    seed = ats_rep.interview_seed
    quotas = QuestionPlanner.plan_question_distribution(analysis, seed, resume)
    core_qs = QuestionEngine.generate_interview_questions(analysis, resume, seed, quotas)
    star_qs, _ = STAREngine.generate_star_questions_and_answers()
    gap_qs, _ = GapHandler.generate_gap_questions_and_answers(analysis, seed)
    return core_qs + star_qs + gap_qs


def test_question_selector_full_interview_first_question(question_pool):
    q, depth = MockQuestionSelector.select_next_question(
        available_questions=question_pool,
        previous_turns=[],
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
    )
    assert q is not None
    assert q.category in (QuestionCategory.HR_SCREENING, QuestionCategory.RESUME_WALKTHROUGH)
    assert depth == 0


def test_question_selector_technical_only_mode(question_pool):
    q, depth = MockQuestionSelector.select_next_question(
        available_questions=question_pool,
        previous_turns=[],
        mode=MockInterviewMode.TECHNICAL_ONLY,
        difficulty=InterviewDifficulty.HARD,
    )
    assert q is not None
    assert q.category in (
        QuestionCategory.JD_TECHNICAL,
        QuestionCategory.BIGQUERY,
        QuestionCategory.AIRFLOW,
        QuestionCategory.DATA_ENGINEERING,
        QuestionCategory.RAG,
        QuestionCategory.GCP,
        QuestionCategory.SQL,
        QuestionCategory.PYTHON,
    )


def test_question_selector_behavioral_mode(question_pool):
    q, depth = MockQuestionSelector.select_next_question(
        available_questions=question_pool,
        previous_turns=[],
        mode=MockInterviewMode.BEHAVIORAL,
    )
    assert q is not None
    assert q.category == QuestionCategory.BEHAVIORAL


def test_question_selector_system_design_mode(question_pool):
    q, depth = MockQuestionSelector.select_next_question(
        available_questions=question_pool,
        previous_turns=[],
        mode=MockInterviewMode.SYSTEM_DESIGN,
    )
    assert q is not None
    # System design or high priority architecture question
    assert q.question != ""
