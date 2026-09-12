import pytest
from pathlib import Path
from careerpilot.core.constants import QuestionCategory, QuestionPriority
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.interview.question_planner import QuestionPlanner
from careerpilot.interview.question_engine import QuestionEngine


def test_interview_question_generation():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)
    ats_report = ATSEvaluator.evaluate_resume(resume, analysis)
    seed = ats_report.interview_seed

    quotas = QuestionPlanner.plan_question_distribution(analysis, seed, resume)
    questions = QuestionEngine.generate_interview_questions(analysis, resume, seed, quotas)

    assert len(questions) >= 20

    # Verify categories present
    cats = {q.category for q in questions}
    assert QuestionCategory.HR_SCREENING in cats
    assert QuestionCategory.RESUME_WALKTHROUGH in cats
    assert QuestionCategory.BIGQUERY in cats or QuestionCategory.AIRFLOW in cats
    assert QuestionCategory.RESUME_DEEP_DIVE in cats
    assert QuestionCategory.PROJECT_DEEP_DIVE in cats
    assert QuestionCategory.CANDIDATE_QUESTIONS in cats

    # Verify priority and reasoning
    for q in questions:
        assert q.question.strip() != ""
        assert q.why_this_question.strip() != ""
        assert q.interviewer_intent.strip() != ""
        assert len(q.expected_topics) > 0

    # Verify critical questions exist
    critical_qs = [q for q in questions if q.priority == QuestionPriority.CRITICAL]
    assert len(critical_qs) >= 3
