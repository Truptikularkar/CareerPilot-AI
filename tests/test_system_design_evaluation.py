import pytest
from careerpilot.core.constants import QuestionCategory, DifficultyLevel, QuestionPriority
from careerpilot.models.interview import InterviewQuestion
from careerpilot.interview.answer_evaluator import AnswerEvaluator


def test_system_design_answer_evaluation():
    q = InterviewQuestion(
        question_id="q_sys_des",
        category=QuestionCategory.SYSTEM_DESIGN,
        subcategory="Event-Driven Ingestion Architecture",
        question="Design an event-driven ingestion pipeline on GCP handling 500k+ daily transactions.",
        difficulty=DifficultyLevel.HARD,
        priority=QuestionPriority.CRITICAL,
        why_this_question="Test system design.",
        source_requirements=["GCP", "BigQuery", "Pub/Sub"],
        candidate_evidence_ids=["EXP_COGNIZANT_001"],
        expected_topics=["GCS", "Pub/Sub", "Cloud Functions", "BigQuery", "DLQ", "Idempotency"],
        interviewer_intent="Verify scalable architecture.",
    )

    answer = (
        "For this system, files land in Google Cloud Storage which triggers a Pub/Sub event. "
        "A serverless Python Cloud Function consumes the notification, validates schema types, and calculates an idempotency hash. "
        "Verified records stream into BigQuery staging tables, and hourly Airflow DAGs perform an atomic MERGE into partitioned production marts. "
        "For unparseable messages, we route to a Dead-Letter Queue (DLQ). We chose Cloud Functions over Dataflow to optimize costs for 500k volume."
    )

    evaluation = AnswerEvaluator.evaluate_answer(question=q, candidate_answer=answer)

    assert evaluation.overall_turn_score >= 75.0
    assert evaluation.system_design_coverage["requirements"] is True or evaluation.system_design_coverage["architecture"] is True

    assert evaluation.system_design_coverage["storage"] is True
    assert evaluation.system_design_coverage["reliability"] is True
    assert evaluation.system_design_coverage["trade_offs"] is True
