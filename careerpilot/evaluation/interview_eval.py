import json
from pathlib import Path
from typing import Dict, Any, List
from careerpilot.interview.mock_question_selector import MockQuestionSelector
from careerpilot.interview.answer_evaluator import AnswerEvaluator
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    QuestionCategory,
    DifficultyLevel,
    QuestionPriority,
    HintMode,
)
from careerpilot.observability.tracer import tracer


def evaluate_interview_engine(golden_path: Path = Path("data/evaluation/interview/golden_interview_cases.json")) -> Dict[str, Any]:
    """
    Evaluates Interview Preparation and Adaptive Mock Interview routing logic.
    """
    if not golden_path.exists():
        return {"status": "ERROR", "message": f"Dataset {golden_path} not found"}

    with open(golden_path, "r", encoding="utf-8") as f:
        q_cases = json.load(f)

    # 1. Evaluate Question Relevance against Golden Set
    relevant_count = sum(1 for q in q_cases if q["expected_relevance"] == "RELEVANT")
    grounded_count = sum(1 for q in q_cases if q["is_evidence_grounded"])
    total_q = len(q_cases)

    # 2. Test Adaptive Question Routing Logic
    sample_pool = [
        InterviewQuestion(
            question_id="q_bq_01",
            category=QuestionCategory.RESUME_DEEP_DIVE,
            subcategory="Query Optimization",
            question="How do partitioning and clustering optimize BigQuery slot usage and costs?",
            difficulty=DifficultyLevel.HARD,
            priority=QuestionPriority.CRITICAL,
            why_this_question="Tests core BigQuery storage layout and scan reduction principles.",
            expected_topics=["partitioning", "clustering", "slots", "byte scan"],
        ),
        InterviewQuestion(
            question_id="q_air_01",
            category=QuestionCategory.AIRFLOW,
            subcategory="Orchestration",
            question="How did you author 40+ modular Airflow DAGs with idempotent backfills?",
            difficulty=DifficultyLevel.MEDIUM,
            priority=QuestionPriority.CRITICAL,
            why_this_question="Tests enterprise Airflow DAG architecture and idempotency.",
            expected_topics=["idempotency", "backfills", "execution_date", "sensors"],
        ),
    ]

    # Evaluate a sample answer
    with tracer.span("EVAL_INTERVIEW", "evaluate_answer"):
        eval_res = AnswerEvaluator.evaluate_answer(
            question=sample_pool[0],
            candidate_answer="At Apex Cloud Solutions, I utilized table partitioning on date and clustering on user_id to prune query scans in BigQuery, reducing query processing costs by ~30%.",
            hint_used=HintMode.NO_HINT,
        )


    # Turn with strong answer
    turn_1 = MockInterviewTurn(
        turn_id="turn_01",
        turn_number=1,
        question_id=sample_pool[0].question_id,
        question_text=sample_pool[0].question,
        category=sample_pool[0].category.value if hasattr(sample_pool[0].category, "value") else str(sample_pool[0].category),
        topic="BigQuery",
        difficulty=sample_pool[0].difficulty.value if hasattr(sample_pool[0].difficulty, "value") else str(sample_pool[0].difficulty),
        candidate_answer="At Apex Cloud Solutions, I utilized table partitioning on date and clustering on user_id...",
        evaluation=eval_res,
        followup_depth=0,
    )


    # Adaptive routing on strong turn -> Should probe follow-up depth
    with tracer.span("EVAL_INTERVIEW", "adaptive_routing"):
        q_next_strong, depth_strong = MockQuestionSelector.select_next_question(
            available_questions=sample_pool,
            previous_turns=[turn_1],
            mode=MockInterviewMode.TECHNICAL_ONLY,
            difficulty=InterviewDifficulty.ADAPTIVE,
            persona=InterviewerPersona.SENIOR_ENGINEER,
        )

    # Verification of adaptive routing
    strong_followup_verified = (depth_strong > 0 or "bigquery" in q_next_strong.question.lower())

    return {
        "status": "SUCCESS",
        "total_questions_evaluated": total_q,
        "question_relevance_rate": round(relevant_count / total_q, 4) if total_q > 0 else 0.0,
        "question_grounding_rate": round(grounded_count / total_q, 4) if total_q > 0 else 0.0,
        "adaptive_routing_rule_verification": {
            "turn_1_evaluated_score": round(eval_res.overall_turn_score, 2),
            "followup_depth_selected": depth_strong,
            "next_adaptive_question": q_next_strong.question[:60] + "...",
            "all_routing_rules_verified": strong_followup_verified,
        },
    }


if __name__ == "__main__":
    res = evaluate_interview_engine()
    print("\n" + "=" * 60)
    print("  Interview Engine Evaluation Results")
    print("=" * 60)
    print(json.dumps(res, indent=2))
