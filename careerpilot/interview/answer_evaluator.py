import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
from careerpilot.core.constants import (
    EvaluationDimension,
    HintMode,
    QuestionCategory,
)
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.mock_interview import AnswerEvaluation, TruthAuditItem
from careerpilot.rag.retriever import retrieve_candidate_evidence
from careerpilot.truth_guard.auditor import TruthAuditor
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class AnswerEvaluator:
    """
    Evaluates candidate interview answers in real time across 10 dimensions,
    extracts technical concepts, audits truth against candidate evidence,
    detects metric mismatches, and generates actionable coaching tips.
    """

    # Domain keyword concepts for technical assessment
    DOMAIN_CONCEPTS: Dict[str, Dict[str, List[str]]] = {
        "bigquery": {
            "required": ["partition", "cluster", "cost", "scan"],
            "advanced": ["pruning", "information_schema", "slot", "cardinality"],
            "misconceptions": ["full table scan is fine", "clustering is always better than partitioning"],
        },
        "airflow": {
            "required": ["dag", "retry", "idempotent", "task"],
            "advanced": ["backoff", "sensor", "backfill", "sla", "autoheal"],
            "misconceptions": ["non-idempotent task is safe", "retries run infinitely"],
        },
        "rag": {
            "required": ["embedding", "retrieval", "vector", "chunk"],
            "advanced": ["faiss", "bm25", "hybrid", "reciprocal rank fusion", "rrf", "grounding"],
            "misconceptions": ["dense search always beats keyword search", "embeddings eliminate hallucinations"],
        },
        "data_quality": {
            "required": ["validation", "null", "anomaly", "schema"],
            "advanced": ["drift", "quarantine", "reconciliation", "bigquery ml"],
            "misconceptions": ["check data only at reporting layer", "ignore schema drift"],
        },
        "pubsub": {
            "required": ["topic", "subscriber", "message", "event"],
            "advanced": ["at-least-once", "deduplication", "dead-letter", "dlq", "idempotency"],
            "misconceptions": ["pubsub guarantees exactly-once delivery by default"],
        },
        "cloud": {
            "required": ["gcp", "bigquery", "storage", "cloud functions"],
            "advanced": ["serverless", "iam", "least privilege", "cost optimization"],
            "misconceptions": ["cloud compute is free when idle", "no need for partition pruning"],
        },
    }

    @classmethod
    def evaluate_answer(
        cls,
        question: InterviewQuestion,
        candidate_answer: str,
        hint_used: HintMode = HintMode.NO_HINT,
        target_role: str = "AI Data Engineer",
        followup_depth: int = 0,
    ) -> AnswerEvaluation:
        eval_id = f"eval_{uuid.uuid4().hex[:8]}"
        ans_text = candidate_answer.strip()
        ans_lower = ans_text.lower()

        # -------------------------------------------------------------
        # 1. Handle "I Don't Know" or blank responses
        # -------------------------------------------------------------
        is_idk = False
        if not ans_text or any(phrase in ans_lower for phrase in ["i don't know", "i do not know", "not sure", "no idea", "pass", "skip"]):
            is_idk = True

        if is_idk:
            dim_scores = {
                EvaluationDimension.TECHNICAL_CORRECTNESS.value: 1.0,
                EvaluationDimension.RELEVANCE.value: 2.0,
                EvaluationDimension.COMPLETENESS.value: 1.0,
                EvaluationDimension.DEPTH.value: 1.0,
                EvaluationDimension.EVIDENCE_GROUNDING.value: 2.5,
                EvaluationDimension.COMMUNICATION_CLARITY.value: 3.5,  # Honesty rewarded
                EvaluationDimension.STRUCTURE.value: 2.0,
                EvaluationDimension.CONFIDENCE.value: 2.0,
                EvaluationDimension.CONCRETE_EXAMPLES.value: 1.0,
                EvaluationDimension.FOLLOW_UP_HANDLING.value: 1.5,
            }
            overall = 35.0
            return AnswerEvaluation(
                evaluation_id=eval_id,
                turn_id=question.question_id,
                dimension_scores=dim_scores,
                overall_turn_score=overall,
                is_i_dont_know=True,
                hint_penalty_applied=0.0,
                correct_concepts=[],
                missing_concepts=question.expected_topics,
                misconceptions=[],
                strengths_observed=["Demonstrated professional honesty rather than fabricating a misleading answer."],
                weaknesses_observed=[f"Unfamiliar with core concepts for '{question.subcategory}'."],
                star_coverage={},
                system_design_coverage={},
                truth_checks=[],
                feedback="Acknowledging when you don't know a concept is respected, but prepare a structured approach to answer what you do know or how you would investigate.",
                coaching_tip=f"For questions like this, state the core fundamental principle first: e.g. '{question.expected_topics[0] if question.expected_topics else 'core architecture'}' and discuss how you would look up the implementation details.",
                suggested_followup_question="Let's step back: what is the fundamental purpose of this component?",
                recommended_difficulty_shift=-1,
            )

        # -------------------------------------------------------------
        # 2. Extract Technical Concepts & Misconceptions
        # -------------------------------------------------------------
        matched_domain = None
        for dom in cls.DOMAIN_CONCEPTS.keys():
            if dom in question.question.lower() or dom in question.subcategory.lower() or dom in ans_lower:
                matched_domain = dom
                break
        if not matched_domain:
            matched_domain = "cloud"

        domain_info = cls.DOMAIN_CONCEPTS[matched_domain]
        correct_concepts = [c for c in domain_info["required"] + domain_info["advanced"] if c in ans_lower]
        missing_concepts = [c for c in domain_info["required"] if c not in ans_lower]
        misconceptions = [m for m in domain_info["misconceptions"] if any(w in ans_lower for w in m.split()[:2])]

        # -------------------------------------------------------------
        # 3. Truth Guard live checks (AWS, Metrics, Personal Projects)
        # -------------------------------------------------------------
        truth_checks: List[TruthAuditItem] = []

        # Check for unverified AWS production claim
        if "aws" in ans_lower and any(w in ans_lower for w in ["production", "engineer", "pipeline", "lead", "architect", "warehouse", "years", "manage", "deploy"]):
            truth_checks.append(
                TruthAuditItem(
                    claim_text="Claim of AWS production experience",
                    status="UNSUPPORTED_CANDIDATE_CLAIM",
                    is_unsupported_claim=True,
                    explanation="Candidate's verified professional production tenure at Cognizant is on GCP. No verified enterprise AWS production records exist.",
                    suggested_framing="Frame your knowledge as transferable cloud concepts: 'My professional production experience is primarily on Google Cloud Platform, but architectural concepts (BigQuery to Redshift, GCS to S3) translate directly.'",
                )
            )


        # Check for metric exaggeration (e.g. claiming 40% or 50% instead of verified 25% or 35%)
        metric_matches = re.findall(r"(\d+)%", ans_text)
        for m_str in metric_matches:
            val = int(m_str)
            if val in (40, 50, 80, 90, 95, 100) and "cost" in ans_lower:
                truth_checks.append(
                    TruthAuditItem(
                        claim_text=f"{val}% cost reduction claim",
                        status="METRIC_MISMATCH",
                        is_metric_mismatch=True,
                        explanation=f"Candidate's verified BigQuery cost reduction is ~25%. Claiming {val}% is unverified.",
                        suggested_framing="State the exact verified metric: 'Achieved a verified ~25% BigQuery cost reduction through table partitioning and clustering.'",
                    )
                )

        # Check for Personal Project misattribution (claiming Local RAG Sandbox was client production)
        if ("rag" in ans_lower or "faiss" in ans_lower) and any(phrase in ans_lower for phrase in ["client production", "enterprise production", "production client", "deployed for client"]):
            truth_checks.append(
                TruthAuditItem(
                    claim_text="Claiming Local RAG Sandbox was client production",
                    status="PERSONAL_PROJECT_MISMATCH",
                    is_personal_project_mismatch=True,
                    explanation="Local RAG & Hybrid Retrieval Sandbox is a personal engineering project, not client enterprise production.",
                    suggested_framing="Explicitly introduce it as an engineering project: 'In my personal engineering project, I built a local offline hybrid search sandbox combining FAISS and BM25.'",
                )
            )

        # -------------------------------------------------------------
        # 4. STAR Behavioral Evaluation (if category is behavioral)
        # -------------------------------------------------------------
        star_coverage = {
            "situation": any(w in ans_lower for w in ["situation", "at cognizant", "when", "context", "problem", "background"]),
            "task": any(w in ans_lower for w in ["task", "objective", "needed to", "goal", "responsibility", "target"]),
            "action": any(w in ans_lower for w in ["i designed", "i implemented", "i built", "i configured", "action", "i automated", "i created"]),
            "result": any(w in ans_lower for w in ["result", "reduced", "achieved", "improved", "saved", "%", "impact", "metric"]),
        }

        # -------------------------------------------------------------
        # 5. System Design Evaluation (if category is system design)
        # -------------------------------------------------------------
        sys_coverage = {
            "requirements": any(w in ans_lower for w in ["requirement", "latency", "sla", "throughput", "scale"]),
            "architecture": any(w in ans_lower for w in ["component", "architecture", "flow", "ingestion", "pipeline"]),
            "storage": any(w in ans_lower for w in ["gcs", "bigquery", "storage", "table", "s3", "warehouse"]),
            "processing": any(w in ans_lower for w in ["cloud function", "python", "sql", "dataflow", "compute"]),
            "reliability": any(w in ans_lower for w in ["retry", "idempotent", "dlq", "dead-letter", "monitoring", "alert"]),
            "trade_offs": any(w in ans_lower for w in ["trade-off", "tradeoff", "versus", "instead of", "chose", "because"]),
        }

        # -------------------------------------------------------------
        # 6. Compute Dimensional Scores (0.0 to 5.0)
        # -------------------------------------------------------------
        # Baseline score derived from concept coverage
        concept_ratio = len(correct_concepts) / max(1, len(domain_info["required"]))
        base_tech = min(5.0, max(1.5, 2.0 + concept_ratio * 3.0))

        # Adjust for length and concrete examples
        word_count = len(ans_text.split())
        has_metrics = bool(re.search(r"\b(\d+[%kK]|~?\d+)\b", ans_text))
        has_cognizant = "cognizant" in ans_lower or "project" in ans_lower

        score_tech = base_tech
        score_relevance = 4.5 if any(topic.lower() in ans_lower for topic in question.expected_topics) or concept_ratio > 0.4 else 3.0
        score_completeness = min(5.0, 2.0 + (len(correct_concepts) / max(1, len(domain_info["required"] + domain_info["advanced"]))) * 3.5)
        score_depth = 4.5 if len(correct_concepts) >= 3 and word_count >= 50 else (3.5 if word_count >= 30 else 2.5)
        score_evidence = 4.8 if has_cognizant and has_metrics and not truth_checks else (3.5 if has_cognizant or has_metrics else 3.0)
        if any(tc.is_unsupported_claim or tc.is_metric_mismatch for tc in truth_checks):
            score_evidence = max(1.5, score_evidence - 2.0)

        score_clarity = 4.5 if 30 <= word_count <= 200 else (3.5 if word_count < 30 else 3.8)
        score_structure = 4.5 if (sum(star_coverage.values()) >= 3 or sum(sys_coverage.values()) >= 3 or word_count >= 60) else 3.5
        score_confidence = 4.5 if not any(w in ans_lower for w in ["maybe", "i think so", "not really sure"]) else 3.0
        score_examples = 4.8 if has_metrics and has_cognizant else (3.5 if has_metrics or has_cognizant else 2.5)
        score_followup = 4.5 if followup_depth > 0 and len(correct_concepts) >= 2 else 4.0

        dim_scores = {
            EvaluationDimension.TECHNICAL_CORRECTNESS.value: round(score_tech, 1),
            EvaluationDimension.RELEVANCE.value: round(score_relevance, 1),
            EvaluationDimension.COMPLETENESS.value: round(score_completeness, 1),
            EvaluationDimension.DEPTH.value: round(score_depth, 1),
            EvaluationDimension.EVIDENCE_GROUNDING.value: round(score_evidence, 1),
            EvaluationDimension.COMMUNICATION_CLARITY.value: round(score_clarity, 1),
            EvaluationDimension.STRUCTURE.value: round(score_structure, 1),
            EvaluationDimension.CONFIDENCE.value: round(score_confidence, 1),
            EvaluationDimension.CONCRETE_EXAMPLES.value: round(score_examples, 1),
            EvaluationDimension.FOLLOW_UP_HANDLING.value: round(score_followup, 1),
        }

        # -------------------------------------------------------------
        # 7. Apply Hint Penalty & Compute Overall Turn Score (0–100%)
        # -------------------------------------------------------------
        hint_penalty = 0.0
        if hint_used == HintMode.SMALL_HINT:
            hint_penalty = 5.0
        elif hint_used == HintMode.FULL_HINT:
            hint_penalty = 15.0

        avg_dim = sum(dim_scores.values()) / len(dim_scores)
        overall_raw = (avg_dim / 5.0) * 100.0
        overall = max(0.0, min(100.0, round(overall_raw - hint_penalty, 1)))

        # -------------------------------------------------------------
        # 8. Strengths, Weaknesses, Feedback & Adaptive Shift
        # -------------------------------------------------------------
        strengths = []
        weaknesses = []

        if score_tech >= 4.0:
            strengths.append(f"Strong grasp of {matched_domain} concepts ({', '.join(correct_concepts[:3])}).")
        if score_examples >= 4.0:
            strengths.append("Effective use of concrete production metrics and real project context.")
        if not strengths:
            strengths.append("Communicated clearly and addressed the core subject matter.")

        if missing_concepts:
            weaknesses.append(f"Omitted key technical terms: {', '.join(missing_concepts)}.")
        if score_depth < 3.0:
            weaknesses.append("Answer remained high-level without explaining underlying mechanics.")
        for tc in truth_checks:
            weaknesses.append(f"Truth Warning: {tc.explanation}")

        # Difficulty shift recommendation
        if overall >= 80.0 and len(correct_concepts) >= 2:
            diff_shift = 1  # Harder / deep follow-up
            followup_q = f"How would you optimize this design further if throughput increased 10x?"
        elif overall < 55.0 or missing_concepts:
            diff_shift = -1  # Easier / conceptual clarification
            followup_q = f"Before going deeper, can you explain the core mechanism of {missing_concepts[0] if missing_concepts else matched_domain}?"
        else:
            diff_shift = 0  # Maintain depth
            followup_q = f"What trade-offs did you consider when implementing this approach?"

        feedback = (
            f"Overall Turn Score: {overall}%. "
            + (f"Great technical precision mentioning {', '.join(correct_concepts[:2])}. " if correct_concepts else "")
            + (f"Consider diving deeper into {', '.join(missing_concepts[:2])}. " if missing_concepts else "")
        )

        coaching_tip = (
            "To elevate this answer to Senior level, clearly state the problem, the specific engineering mechanism (with numbers/metrics), and the measurable business outcome."
            if overall < 85.0
            else "Excellent response! Keep framing design choices with explicit trade-offs and cost/latency impacts."
        )
        if truth_checks:
            coaching_tip = truth_checks[0].suggested_framing or coaching_tip

        return AnswerEvaluation(
            evaluation_id=eval_id,
            turn_id=question.question_id,
            dimension_scores=dim_scores,
            overall_turn_score=overall,
            is_i_dont_know=False,
            hint_penalty_applied=hint_penalty,
            correct_concepts=correct_concepts,
            missing_concepts=missing_concepts,
            misconceptions=misconceptions,
            strengths_observed=strengths,
            weaknesses_observed=weaknesses,
            star_coverage=star_coverage,
            system_design_coverage=sys_coverage,
            truth_checks=truth_checks,
            feedback=feedback,
            coaching_tip=coaching_tip,
            suggested_followup_question=followup_q,
            recommended_difficulty_shift=diff_shift,
        )
