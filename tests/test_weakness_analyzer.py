import pytest
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation
from careerpilot.interview.weakness_analyzer import WeaknessAnalyzer


def test_weakness_analyzer_detects_gap_and_strength():
    # Turn 1: Strong BigQuery turn
    t1 = MockInterviewTurn(
        turn_id="t1",
        turn_number=1,
        question_id="q1",
        question_text="Explain BigQuery partitioning.",
        category="BIGQUERY",
        topic="BigQuery",
        difficulty="MEDIUM",
        followup_depth=0,
        candidate_answer="Partitioning date blocks reduces byte scans by 25%.",
        evaluation=AnswerEvaluation(
            evaluation_id="e1",
            turn_id="q1",
            overall_turn_score=88.0,
            strengths_observed=["Strong grasp of BigQuery partitioning and cost reduction."],
            weaknesses_observed=[],
        ),
    )

    # Turn 2: Weak Airflow turn
    t2 = MockInterviewTurn(
        turn_id="t2",
        turn_number=2,
        question_id="q2",
        question_text="How do you handle Airflow DAG failure retries and idempotency?",
        category="AIRFLOW",
        topic="Airflow",
        difficulty="HARD",
        followup_depth=0,
        candidate_answer="I just restart the DAG when it fails.",
        evaluation=AnswerEvaluation(
            evaluation_id="e2",
            turn_id="q2",
            overall_turn_score=48.0,
            missing_concepts=["idempotent", "retry", "backoff"],
            strengths_observed=[],
            weaknesses_observed=["Omitted key technical terms: idempotent, retry."],
        ),
    )

    weaknesses, strengths, recs = WeaknessAnalyzer.analyze_session([t1, t2])

    assert len(strengths) >= 1
    assert strengths[0].topic == "BigQuery"

    assert len(weaknesses) >= 1
    assert weaknesses[0].topic == "Airflow"
    assert "idempotent" in weaknesses[0].description.lower() or "airflow" in weaknesses[0].suggested_remedy.lower()

    assert len(recs) >= 1
    assert any("airflow" in r.lower() for r in recs)
