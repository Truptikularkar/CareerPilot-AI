import pytest
from careerpilot.core.constants import QuestionCategory, DifficultyLevel, QuestionPriority
from careerpilot.models.interview import InterviewQuestion
from careerpilot.interview.answer_evaluator import AnswerEvaluator


def test_behavioral_star_answer_evaluation():
    q = InterviewQuestion(
        question_id="q_star_test",
        category=QuestionCategory.BEHAVIORAL,
        subcategory="Production Incident Management",
        question="Tell me about a production pipeline failure you faced and how you handled it.",
        difficulty=DifficultyLevel.MEDIUM,
        priority=QuestionPriority.HIGH,
        why_this_question="Test problem solving.",
        source_requirements=["Incident Response"],
        candidate_evidence_ids=["PROJ_AUTOHEAL_AGENT"],
        expected_topics=["Situation", "Action", "Result"],
        interviewer_intent="Verify resilience.",
    )

    answer = (
        "Situation: At Cognizant, daily Airflow DAGs failed intermittently due to transient connection timeouts during peak volume. "
        "Task: I needed to automate error triaging to reduce on-call incident response time. "
        "Action: I built an AI AutoHeal agent using Google Gemini API to parse worker logs and trigger exponential backoff retries for transient errors. "
        "Result: The agent resolved ~75% of transient errors automatically and cut on-call response time by ~60%."
    )

    evaluation = AnswerEvaluator.evaluate_answer(question=q, candidate_answer=answer)

    assert evaluation.overall_turn_score >= 85.0
    assert evaluation.star_coverage["situation"] is True
    assert evaluation.star_coverage["task"] is True
    assert evaluation.star_coverage["action"] is True
    assert evaluation.star_coverage["result"] is True
    assert len(evaluation.truth_checks) == 0
