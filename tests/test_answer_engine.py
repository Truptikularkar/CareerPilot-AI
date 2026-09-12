import pytest
from pathlib import Path
from careerpilot.models.interview import InterviewQuestion
from careerpilot.core.constants import QuestionCategory, QuestionPriority, DifficultyLevel
from careerpilot.interview.answer_engine import AnswerEngine


def test_answer_engine_bigquery_and_metrics():
    q = InterviewQuestion(
        question_id="test_q_bq",
        category=QuestionCategory.BIGQUERY,
        subcategory="BigQuery Architecture",
        question="How did you optimize BigQuery and reduce query costs?",
        difficulty=DifficultyLevel.MEDIUM,
        priority=QuestionPriority.CRITICAL,
        why_this_question="Test cost optimization.",
        source_requirements=["BigQuery", "SQL"],
        candidate_evidence_ids=["EXP_COGNIZANT_005"],
        expected_topics=["Partitioning", "Clustering", "25% cost reduction"],
        interviewer_intent="Verify BQ optimization.",
    )

    ans = AnswerEngine.generate_answer_for_question(q)

    assert ans.question_id == "test_q_bq"
    assert "partitioning" in ans.direct_answer.lower()
    assert "clustering" in ans.direct_answer.lower()
    assert "25%" in ans.result_impact
    assert ans.short_version != ""
    assert ans.standard_version != ""
    assert ans.detailed_version != ""
    assert ans.evidence_status == "VERIFIED"


def test_answer_engine_airflow_and_autoheal():
    q = InterviewQuestion(
        question_id="test_q_af",
        category=QuestionCategory.AIRFLOW,
        subcategory="Airflow Operations",
        question="How did your self-healing Airflow agent resolve transient pipeline failures?",
        difficulty=DifficultyLevel.HARD,
        priority=QuestionPriority.CRITICAL,
        why_this_question="Test GenAI operations.",
        source_requirements=["Apache Airflow", "Gemini API"],
        candidate_evidence_ids=["PROJ_AUTOHEAL_AGENT"],
        expected_topics=["Log parsing", "75% auto-heal"],
        interviewer_intent="Verify auto-healing agent.",
    )

    ans = AnswerEngine.generate_answer_for_question(q)
    assert "75%" in ans.result_impact
    assert "60%" in ans.result_impact
    assert len(ans.grounded_evidence_ids) > 0
