import pytest
from careerpilot.interview.star_engine import STAREngine


def test_star_engine_grounded_stories():
    questions, star_answers = STAREngine.generate_star_questions_and_answers()

    assert len(questions) >= 4
    assert len(star_answers) >= 4

    # Verify Data Quality STAR story
    dq_star = next((s for s in star_answers if "35%" in s.result), None)
    assert dq_star is not None
    assert "Cognizant" in dq_star.situation
    assert "BigQuery" in dq_star.action
    assert dq_star.is_insufficient_evidence is False

    # Verify Self-Healing Failure Triage STAR story
    heal_star = next((s for s in star_answers if "75%" in s.result), None)
    assert heal_star is not None
    assert "Gemini" in heal_star.action or "Vertex" in heal_star.action
    assert heal_star.is_insufficient_evidence is False


def test_star_engine_insufficient_evidence_handling():
    questions, star_answers = STAREngine.generate_star_questions_and_answers()

    # Verify that unevidenced executive vendor negotiation returns INSUFFICIENT_EVIDENCE
    insufficient = next((s for s in star_answers if s.is_insufficient_evidence is True), None)
    assert insufficient is not None
    assert insufficient.situation == "INSUFFICIENT_EVIDENCE"
    assert insufficient.insufficient_evidence_reason is not None
    assert "Programmer Analyst" in insufficient.insufficient_evidence_reason
