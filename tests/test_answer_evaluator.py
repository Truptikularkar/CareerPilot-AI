import pytest
from careerpilot.core.constants import QuestionCategory, DifficultyLevel, QuestionPriority, HintMode
from careerpilot.models.interview import InterviewQuestion
from careerpilot.interview.answer_evaluator import AnswerEvaluator


@pytest.fixture
def bigquery_question():
    return InterviewQuestion(
        question_id="q_eval_bq",
        category=QuestionCategory.BIGQUERY,
        subcategory="BigQuery Architecture",
        question="How do partitioning and clustering in BigQuery improve query performance and reduce compute costs?",
        difficulty=DifficultyLevel.MEDIUM,
        priority=QuestionPriority.CRITICAL,
        why_this_question="Test core DW knowledge.",
        source_requirements=["BigQuery", "SQL"],
        candidate_evidence_ids=["EXP_COGNIZANT_005"],
        expected_topics=["Partitioning", "Clustering", "Partition pruning", "Cost reduction"],
        interviewer_intent="Verify BQ tuning.",
    )


def test_answer_evaluator_strong_answer(bigquery_question):
    answer = (
        "Partitioning physically divides tables by ingestion date, allowing BigQuery to execute partition pruning "
        "and scan only the required date slices rather than the full table. Clustering sorts and colocates data based on "
        "high-cardinality keys like customer_id. At Cognizant, enforcing partition filters in Airflow DAGs across tables with ~500k+ daily records "
        "achieved a verified ~25% reduction in query processing costs."
    )
    evaluation = AnswerEvaluator.evaluate_answer(
        question=bigquery_question,
        candidate_answer=answer,
        hint_used=HintMode.NO_HINT,
    )

    assert evaluation.overall_turn_score >= 80.0
    assert evaluation.is_i_dont_know is False
    assert len(evaluation.correct_concepts) >= 2
    assert "partition" in evaluation.correct_concepts
    assert len(evaluation.truth_checks) == 0
    assert evaluation.recommended_difficulty_shift == 1


def test_answer_evaluator_weak_answer(bigquery_question):
    answer = "I optimized the queries to make them faster."
    evaluation = AnswerEvaluator.evaluate_answer(
        question=bigquery_question,
        candidate_answer=answer,
    )

    assert evaluation.overall_turn_score < 70.0
    assert len(evaluation.missing_concepts) > 0
    assert evaluation.recommended_difficulty_shift <= 0


def test_answer_evaluator_i_dont_know(bigquery_question):
    answer = "I don't know the exact internal difference between them."
    evaluation = AnswerEvaluator.evaluate_answer(
        question=bigquery_question,
        candidate_answer=answer,
    )

    assert evaluation.is_i_dont_know is True
    assert evaluation.overall_turn_score <= 50.0
    assert evaluation.recommended_difficulty_shift == -1
    assert "honesty" in evaluation.strengths_observed[0].lower()


def test_answer_evaluator_hint_penalties(bigquery_question):
    answer = "Partitioning segments data and reduces scan costs."
    eval_no_hint = AnswerEvaluator.evaluate_answer(bigquery_question, answer, HintMode.NO_HINT)
    eval_small_hint = AnswerEvaluator.evaluate_answer(bigquery_question, answer, HintMode.SMALL_HINT)
    eval_full_hint = AnswerEvaluator.evaluate_answer(bigquery_question, answer, HintMode.FULL_HINT)

    assert eval_small_hint.hint_penalty_applied == 5.0
    assert eval_full_hint.hint_penalty_applied == 15.0
    assert eval_small_hint.overall_turn_score < eval_no_hint.overall_turn_score
    assert eval_full_hint.overall_turn_score < eval_small_hint.overall_turn_score


def test_answer_evaluator_truth_guard_aws_claim(bigquery_question):
    answer = "As lead AWS data engineer managing Redshift and Glue production warehouses for 3 years, I partitioned data."
    evaluation = AnswerEvaluator.evaluate_answer(bigquery_question, answer)

    assert len(evaluation.truth_checks) >= 1
    unsupported = next((tc for tc in evaluation.truth_checks if tc.is_unsupported_claim), None)
    assert unsupported is not None
    assert "AWS production" in unsupported.claim_text


def test_answer_evaluator_truth_guard_metric_mismatch(bigquery_question):
    answer = "At Cognizant, I reduced BigQuery query processing costs by 40% using clustering."
    evaluation = AnswerEvaluator.evaluate_answer(bigquery_question, answer)

    assert len(evaluation.truth_checks) >= 1
    metric_mm = next((tc for tc in evaluation.truth_checks if tc.is_metric_mismatch), None)
    assert metric_mm is not None
    assert "40%" in metric_mm.claim_text


def test_answer_evaluator_personal_project_mismatch():
    q = InterviewQuestion(
        question_id="q_rag",
        category=QuestionCategory.RAG,
        subcategory="Hybrid RAG Architecture",
        question="Explain your hybrid search implementation.",
        difficulty=DifficultyLevel.HARD,
        priority=QuestionPriority.HIGH,
        why_this_question="Test RAG.",
        source_requirements=["RAG"],
        candidate_evidence_ids=["PROJ_LOCAL_RAG"],
        expected_topics=["FAISS", "BM25", "RRF"],
        interviewer_intent="Verify search pipeline.",
    )
    answer = "In my enterprise client production RAG system, I deployed FAISS and BM25 for paying customers."
    evaluation = AnswerEvaluator.evaluate_answer(q, answer)

    assert len(evaluation.truth_checks) >= 1
    proj_mm = next((tc for tc in evaluation.truth_checks if tc.is_personal_project_mismatch), None)
    assert proj_mm is not None
