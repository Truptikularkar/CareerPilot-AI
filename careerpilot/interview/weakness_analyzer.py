from typing import List, Dict, Any, Tuple
from careerpilot.models.mock_interview import (
    MockInterviewTurn,
    WeaknessItem,
    StrengthItem,
    AnswerEvaluation,
)
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class WeaknessAnalyzer:
    """
    Analyzes multi-turn candidate responses to detect persistent weaknesses,
    extract standout strengths, and formulate actionable study recommendations.
    """

    @classmethod
    def analyze_session(
        cls,
        turns: List[MockInterviewTurn],
    ) -> Tuple[List[WeaknessItem], List[StrengthItem], List[str]]:
        weaknesses: List[WeaknessItem] = []
        strengths: List[StrengthItem] = []
        study_recommendations: List[str] = []

        topic_evals: Dict[str, List[AnswerEvaluation]] = {}
        for t in turns:
            if t.evaluation:
                topic_evals.setdefault(t.topic or t.category, []).append(t.evaluation)

        for topic, evals in topic_evals.items():
            avg_score = sum(e.overall_turn_score for e in evals) / len(evals)
            all_missing = [c for e in evals for c in e.missing_concepts]
            all_weaknesses = [w for e in evals for w in e.weaknesses_observed]
            all_strengths = [s for e in evals for s in e.strengths_observed]
            turn_ids = [e.turn_id for e in evals]

            # ---------------------------------------------------------
            # Weakness Identification
            # ---------------------------------------------------------
            if avg_score < 65.0 or all_missing or any("Truth Warning" in w for w in all_weaknesses):
                desc = f"Candidate scored {avg_score:.1f}% on {topic}. "
                if all_missing:
                    desc += f"Omitted core technical concepts: {', '.join(set(all_missing[:3]))}. "
                if any("Truth Warning" in w for w in all_weaknesses):
                    desc += "Contains unverified experience or metric claims."

                remedy = f"Review foundational and architectural concepts for {topic}. Practice explaining trade-offs and underlying mechanics."
                if "airflow" in topic.lower():
                    remedy = "Deep-dive into Airflow failure handling, exponential backoff retries, and task idempotency."
                elif "bigquery" in topic.lower() or "sql" in topic.lower():
                    remedy = "Practice query profiling in BigQuery Information Schema and sort/cluster key optimization."
                elif "rag" in topic.lower():
                    remedy = "Review hybrid search mechanics: Reciprocal Rank Fusion formula and dense vs sparse search trade-offs."
                elif "cloud" in topic.lower() or "aws" in topic.lower():
                    remedy = "Rehearse honest GCP-to-AWS cloud conceptual mapping without claiming unverified AWS production experience."

                weaknesses.append(
                    WeaknessItem(
                        topic=topic,
                        description=desc.strip(),
                        evidence_turn_ids=turn_ids,
                        suggested_remedy=remedy,
                    )
                )
                study_recommendations.append(remedy)

            # ---------------------------------------------------------
            # Strength Identification
            # ---------------------------------------------------------
            if avg_score >= 80.0:
                desc = f"High proficiency ({avg_score:.1f}%) on {topic}. "
                if all_strengths:
                    desc += f"Standout performance: {all_strengths[0]}"
                strengths.append(
                    StrengthItem(
                        topic=topic,
                        description=desc.strip(),
                        evidence_turn_ids=turn_ids,
                    )
                )

        # Fallback study recommendation if no weaknesses found
        if not study_recommendations:
            study_recommendations.append("Conduct a final end-to-end mock simulation under timed constraints to solidify interview endurance.")

        return weaknesses, strengths, study_recommendations
