import pytest
from pathlib import Path
from careerpilot.core.constants import MockInterviewMode, InterviewDifficulty, InterviewerPersona, QuestionCategory
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation
from careerpilot.interview.mock_question_selector import MockQuestionSelector


@pytest.fixture
def mock_questions():
    return [
        InterviewQuestion(
            question_id="q_bq_1",
            category=QuestionCategory.BIGQUERY,
            subcategory="BigQuery Architecture",
            question="What is BigQuery partitioning?",
            why_this_question="Test DW.",
            source_requirements=["BigQuery"],
            candidate_evidence_ids=[],
            expected_topics=["Partitioning", "Pruning"],
            interviewer_intent="Probe storage.",
        ),
        InterviewQuestion(
            question_id="q_af_1",
            category=QuestionCategory.AIRFLOW,
            subcategory="Airflow Operations",
            question="How do you ensure DAG idempotency in Airflow?",
            why_this_question="Test orchestration.",
            source_requirements=["Airflow"],
            candidate_evidence_ids=[],
            expected_topics=["Idempotency", "Retries"],
            interviewer_intent="Probe failure handling.",
        ),
        InterviewQuestion(
            question_id="q_rag_1",
            category=QuestionCategory.RAG,
            subcategory="RAG Architecture",
            question="Explain hybrid retrieval using FAISS and BM25.",
            why_this_question="Test GenAI.",
            source_requirements=["RAG"],
            candidate_evidence_ids=[],
            expected_topics=["FAISS", "BM25", "RRF"],
            interviewer_intent="Probe search.",
        ),
    ]


def test_adaptive_routing_strong_answer_triggers_followup(mock_questions):
    # Candidate gives a strong answer (score 88%)
    t1 = MockInterviewTurn(
        turn_id="t1",
        turn_number=1,
        question_id="q_bq_1",
        question_text="What is BigQuery partitioning?",
        category="BIGQUERY",
        topic="BigQuery Architecture",
        difficulty="MEDIUM",
        followup_depth=0,
        candidate_answer="Partitioning divides tables by date blocks, enabling partition pruning and cost reduction.",
        evaluation=AnswerEvaluation(
            evaluation_id="e1",
            turn_id="q_bq_1",
            overall_turn_score=88.0,
            correct_concepts=["partition", "pruning", "cost"],
            missing_concepts=[],
            suggested_followup_question="How would you design table clustering within those partitions for customer queries?",
            recommended_difficulty_shift=1,
        ),
    )

    next_q, next_depth = MockQuestionSelector.select_next_question(
        available_questions=mock_questions,
        previous_turns=[t1],
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
    )

    # Next question must be a deeper follow-up at Depth 1
    assert next_depth == 1
    assert next_q.category == QuestionCategory.FOLLOW_UP
    assert "clustering" in next_q.question.lower() or "optimize" in next_q.question.lower()


def test_adaptive_routing_weak_answer_triggers_clarification(mock_questions):
    # Candidate gives a weak answer missing concepts (score 42%)
    t1 = MockInterviewTurn(
        turn_id="t1",
        turn_number=1,
        question_id="q_af_1",
        question_text="How do you ensure DAG idempotency in Airflow?",
        category="AIRFLOW",
        topic="Airflow Operations",
        difficulty="HARD",
        followup_depth=0,
        candidate_answer="I make sure the task runs without errors.",
        evaluation=AnswerEvaluation(
            evaluation_id="e1",
            turn_id="q_af_1",
            overall_turn_score=42.0,
            correct_concepts=[],
            missing_concepts=["idempotency"],
            suggested_followup_question="What does idempotency mean when re-running historical DAGs?",
            recommended_difficulty_shift=-1,
        ),
    )

    next_q, next_depth = MockQuestionSelector.select_next_question(
        available_questions=mock_questions,
        previous_turns=[t1],
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
    )

    # Triggers conceptual clarification at Depth 1
    assert next_depth == 1
    assert next_q.category == QuestionCategory.FOLLOW_UP
    assert "idempotency" in next_q.question.lower() or "purpose" in next_q.question.lower()


def test_adaptive_routing_switches_topic_after_depth_reached(mock_questions):
    # Turn at Depth 3 completed with high score
    t1 = MockInterviewTurn(
        turn_id="t1",
        turn_number=3,
        question_id="q_bq_1",
        question_text="Deep dive on BigQuery clustering.",
        category="BIGQUERY",
        topic="BigQuery Architecture",
        difficulty="EXPERT",
        followup_depth=3,
        evaluation=AnswerEvaluation(
            evaluation_id="e3",
            turn_id="q_bq_1",
            overall_turn_score=92.0,
        ),
    )

    next_q, next_depth = MockQuestionSelector.select_next_question(
        available_questions=mock_questions,
        previous_turns=[t1],
        mode=MockInterviewMode.TECHNICAL_ONLY,
        difficulty=InterviewDifficulty.ADAPTIVE,
    )

    # Stops drilling BigQuery and switches to a new unasked topic at Depth 0
    assert next_depth == 0
    assert next_q.question_id in ("q_af_1", "q_rag_1")
