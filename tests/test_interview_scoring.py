import pytest
from pathlib import Path
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation, TruthAuditItem
from careerpilot.core.constants import EvaluationDimension
from careerpilot.interview.interview_scorer import InterviewScorer


def test_interview_scorer_aggregation():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)

    t1 = MockInterviewTurn(
        turn_id="t1",
        turn_number=1,
        question_id="q1",
        question_text="Explain BigQuery partitioning.",
        category="BIGQUERY",
        topic="BigQuery",
        difficulty="MEDIUM",
        followup_depth=0,
        evaluation=AnswerEvaluation(
            evaluation_id="e1",
            turn_id="q1",
            overall_turn_score=90.0,
            dimension_scores={
                EvaluationDimension.TECHNICAL_CORRECTNESS.value: 4.5,
                EvaluationDimension.COMMUNICATION_CLARITY.value: 4.5,
                EvaluationDimension.STRUCTURE.value: 4.5,
                EvaluationDimension.CONFIDENCE.value: 4.5,
                EvaluationDimension.DEPTH.value: 4.5,
                EvaluationDimension.FOLLOW_UP_HANDLING.value: 4.5,
                EvaluationDimension.EVIDENCE_GROUNDING.value: 4.8,
            },
            truth_checks=[],
        ),
    )

    t2 = MockInterviewTurn(
        turn_id="t2",
        turn_number=2,
        question_id="q2",
        question_text="How did you build the AI autoheal agent?",
        category="PROJECT_DEEP_DIVE",
        topic="AutoHeal Agent",
        difficulty="HARD",
        followup_depth=0,
        evaluation=AnswerEvaluation(
            evaluation_id="e2",
            turn_id="q2",
            overall_turn_score=85.0,
            dimension_scores={
                EvaluationDimension.TECHNICAL_CORRECTNESS.value: 4.2,
                EvaluationDimension.COMMUNICATION_CLARITY.value: 4.2,
                EvaluationDimension.STRUCTURE.value: 4.2,
                EvaluationDimension.CONFIDENCE.value: 4.2,
                EvaluationDimension.DEPTH.value: 4.2,
                EvaluationDimension.FOLLOW_UP_HANDLING.value: 4.2,
                EvaluationDimension.EVIDENCE_GROUNDING.value: 4.5,
            },
            truth_checks=[],
        ),
    )

    scores, topic_mastery, jd_cov, chal, well, poorly, truth_c = InterviewScorer.score_session(
        turns=[t1, t2],
        job_analysis=analysis,
    )

    assert scores["overall_score"] >= 80.0
    assert scores["technical_score"] >= 80.0
    assert scores["experience_accuracy_score"] == 100.0
    assert len(topic_mastery) >= 2
    assert "BigQuery" in topic_mastery
    assert topic_mastery["BigQuery"].status in ("MASTERED", "PROFICIENT")
    assert len(well) == 2
    assert len(poorly) == 0


def test_interview_scorer_penalizes_unsupported_claims():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)

    t1 = MockInterviewTurn(
        turn_id="t1",
        turn_number=1,
        question_id="q1",
        question_text="Explain your cloud experience.",
        category="GCP",
        topic="Cloud",
        difficulty="MEDIUM",
        followup_depth=0,
        evaluation=AnswerEvaluation(
            evaluation_id="e1",
            turn_id="q1",
            overall_turn_score=60.0,
            dimension_scores={EvaluationDimension.TECHNICAL_CORRECTNESS.value: 3.0},
            truth_checks=[
                TruthAuditItem(
                    claim_text="AWS production",
                    status="UNSUPPORTED_CANDIDATE_CLAIM",
                    is_unsupported_claim=True,
                )
            ],
        ),
    )

    scores, _, _, _, _, _, truth_c = InterviewScorer.score_session(
        turns=[t1],
        job_analysis=analysis,
    )

    assert scores["experience_accuracy_score"] == 80.0  # Penalized 20 points
    assert len(truth_c) == 1
