from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import EvaluationDimension, MockInterviewMode, QuestionCategory
from careerpilot.models.mock_interview import (
    MockInterviewTurn,
    TopicMastery,
    JDCoverageItem,
    TruthAuditItem,
)
from careerpilot.models.job import JobAnalysisResult
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class InterviewScorer:
    """
    Computes deterministic multi-dimensional scores, topic mastery levels,
    and JD coverage tracking across an entire mock interview session.
    """

    @classmethod
    def score_session(
        cls,
        turns: List[MockInterviewTurn],
        job_analysis: JobAnalysisResult,
    ) -> Tuple[Dict[str, float], Dict[str, TopicMastery], List[JDCoverageItem], List[str], List[str], List[str], List[TruthAuditItem]]:
        scores: Dict[str, float] = {
            "overall_score": 0.0,
            "technical_score": 0.0,
            "communication_score": 0.0,
            "resume_knowledge_score": 0.0,
            "project_score": 0.0,
            "system_design_score": 0.0,
            "behavioral_score": 0.0,
            "problem_solving_score": 0.0,
            "experience_accuracy_score": 100.0,
        }

        if not turns:
            return scores, {}, [], [], [], [], []

        evals = [t.evaluation for t in turns if t.evaluation]
        if not evals:
            return scores, {}, [], [], [], [], []

        # -------------------------------------------------------------
        # 1. Calculate Component Scores
        # -------------------------------------------------------------
        tech_dims = [
            e.dimension_scores.get(EvaluationDimension.TECHNICAL_CORRECTNESS.value, 3.0)
            for e in evals
        ]
        comm_dims = [
            (
                e.dimension_scores.get(EvaluationDimension.COMMUNICATION_CLARITY.value, 3.5)
                + e.dimension_scores.get(EvaluationDimension.STRUCTURE.value, 3.5)
                + e.dimension_scores.get(EvaluationDimension.CONFIDENCE.value, 3.5)
            ) / 3.0
            for e in evals
        ]
        prob_dims = [
            (
                e.dimension_scores.get(EvaluationDimension.DEPTH.value, 3.0)
                + e.dimension_scores.get(EvaluationDimension.FOLLOW_UP_HANDLING.value, 3.0)
            ) / 2.0
            for e in evals
        ]
        evid_dims = [
            e.dimension_scores.get(EvaluationDimension.EVIDENCE_GROUNDING.value, 3.5)
            for e in evals
        ]

        scores["technical_score"] = round((sum(tech_dims) / len(tech_dims) / 5.0) * 100.0, 1)
        scores["communication_score"] = round((sum(comm_dims) / len(comm_dims) / 5.0) * 100.0, 1)
        scores["problem_solving_score"] = round((sum(prob_dims) / len(prob_dims) / 5.0) * 100.0, 1)
        scores["resume_knowledge_score"] = round((sum(evid_dims) / len(evid_dims) / 5.0) * 100.0, 1)

        # Category-specific scores
        proj_turns = [t for t in turns if t.category == QuestionCategory.PROJECT_DEEP_DIVE.value and t.evaluation]
        scores["project_score"] = round(sum(t.evaluation.overall_turn_score for t in proj_turns) / len(proj_turns), 1) if proj_turns else scores["technical_score"]

        sys_turns = [t for t in turns if t.category == QuestionCategory.SYSTEM_DESIGN.value and t.evaluation]
        scores["system_design_score"] = round(sum(t.evaluation.overall_turn_score for t in sys_turns) / len(sys_turns), 1) if sys_turns else scores["problem_solving_score"]

        behav_turns = [t for t in turns if t.category == QuestionCategory.BEHAVIORAL.value and t.evaluation]
        scores["behavioral_score"] = round(sum(t.evaluation.overall_turn_score for t in behav_turns) / len(behav_turns), 1) if behav_turns else scores["communication_score"]

        # Experience Accuracy Score (Penalize for Truth Violations)
        all_truth_checks = [tc for e in evals for tc in e.truth_checks]
        unverified_count = sum(1 for tc in all_truth_checks if tc.is_unsupported_claim or tc.is_metric_mismatch or tc.is_personal_project_mismatch)
        scores["experience_accuracy_score"] = max(0.0, round(100.0 - (unverified_count * 20.0), 1))

        # Overall Session Weighted Score
        raw_overall = sum(e.overall_turn_score for e in evals) / len(evals)
        scores["overall_score"] = max(0.0, min(100.0, round((raw_overall * 0.85) + (scores["experience_accuracy_score"] * 0.15), 1)))

        # -------------------------------------------------------------
        # 2. Topic Mastery Calculation
        # -------------------------------------------------------------
        topic_mastery: Dict[str, TopicMastery] = {}
        for t in turns:
            if not t.evaluation:
                continue
            top = t.topic or t.category
            if top not in topic_mastery:
                topic_mastery[top] = TopicMastery(topic=top, mastery_score=0.0, questions_asked=0)

            curr = topic_mastery[top]
            curr.questions_asked += 1
            curr_dim_avg = sum(t.evaluation.dimension_scores.values()) / len(t.evaluation.dimension_scores)
            curr.mastery_score = round(((curr.mastery_score * (curr.questions_asked - 1)) + curr_dim_avg) / curr.questions_asked, 1)

            if curr.mastery_score >= 4.2:
                curr.status = "MASTERED"
            elif curr.mastery_score >= 3.5:
                curr.status = "PROFICIENT"
            elif curr.mastery_score >= 2.5:
                curr.status = "DEVELOPING"
            else:
                curr.status = "WEAK"

        # -------------------------------------------------------------
        # 3. JD Requirement Coverage Tracking
        # -------------------------------------------------------------
        jd_coverage: List[JDCoverageItem] = []
        tested_text = " ".join(t.question_text.lower() + " " + t.topic.lower() for t in turns)

        for req in job_analysis.requirements:
            skill = req.normalized_skill
            status = "NOT_COVERED"
            score_val = None

            if skill.lower() in tested_text:
                status = "COVERED"
                matching_turns = [t for t in turns if skill.lower() in t.question_text.lower() or skill.lower() in t.topic.lower()]
                if matching_turns and matching_turns[0].evaluation:
                    score_val = matching_turns[0].evaluation.overall_turn_score
            elif any(w in tested_text for w in skill.lower().split() if len(w) > 3):
                status = "PARTIALLY_COVERED"

            jd_coverage.append(
                JDCoverageItem(
                    skill_or_requirement=skill,
                    importance=req.importance.value,
                    status=status,
                    score=score_val,
                )
            )

        # -------------------------------------------------------------
        # 4. Question Performance Categorization
        # -------------------------------------------------------------
        well_answered = [t.question_text for t in turns if t.evaluation and t.evaluation.overall_turn_score >= 80.0]
        poorly_answered = [t.question_text for t in turns if t.evaluation and (t.evaluation.overall_turn_score < 60.0 or t.evaluation.is_i_dont_know)]
        challenging_qs = [t.question_text for t in turns if t.difficulty in ("HARD", "EXPERT") or t.followup_depth >= 2]

        return scores, topic_mastery, jd_coverage, challenging_qs, well_answered, poorly_answered, all_truth_checks
