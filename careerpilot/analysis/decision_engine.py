from typing import List, Tuple, Optional
from careerpilot.core.config import settings
from careerpilot.core.constants import (
    DecisionRecommendation,
    RiskSeverity,
    MatchStatus,
    RequirementImportance,
    TaxonomyCategory,
    CloudTransferabilityStatus,
    RoleCategory,
)
from careerpilot.models.job import (
    JobDescription,
    RoleClassification,
    RoleReality,
    SeniorityDetection,
    CloudTransferability,
    RequirementMatch,
    FitScoreBreakdown,
    RiskItem,
    JobAnalysisResult,
)
from careerpilot.models.candidate import CandidateProfile
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """
    Deterministic, explainable decision engine that evaluates fit scores,
    critical risks, must-have coverage, and candidate career preferences
    to recommend APPLY, REVIEW, or SKIP.
    """

    @classmethod
    def evaluate_decision(
        cls,
        jd: JobDescription,
        role_class: RoleClassification,
        role_reality: RoleReality,
        cloud_eval: CloudTransferability,
        matches: List[RequirementMatch],
        fit_score: FitScoreBreakdown,
        risks: List[RiskItem],
        candidate_profile: Optional[CandidateProfile] = None,
    ) -> JobAnalysisResult:
        # Extract strengths & gaps
        strengths = [
            m.requirement.normalized_skill
            for m in matches
            if m.match_status == MatchStatus.MATCH
        ]
        strengths = list(dict.fromkeys(strengths))

        gaps = [
            m.requirement.normalized_skill
            for m in matches
            if m.match_status == MatchStatus.GAP
        ]
        gaps = list(dict.fromkeys(gaps))

        transferable_skills = []
        if cloud_eval.transferability_status == CloudTransferabilityStatus.TRANSFERABLE:
            transferable_skills.append("GCP Data Engineering -> AWS (BigQuery/Airflow -> Redshift/Glue/S3)")

        # Count risk severities
        critical_risks = [r for r in risks if r.severity == RiskSeverity.CRITICAL]
        high_risks = [r for r in risks if r.severity == RiskSeverity.HIGH]

        # Count technical must-have gaps (safeguarding against soft skills or unparsed lines)
        must_have_gaps = [
            m for m in matches
            if m.requirement.importance == RequirementImportance.MUST_HAVE
            and m.match_status == MatchStatus.GAP
            and m.requirement.category not in (TaxonomyCategory.SOFT_SKILL, TaxonomyCategory.OTHER)
        ]

        score = fit_score.total_weighted_score
        apply_thresh = settings.DECISION_APPLY_THRESHOLD
        review_thresh = settings.DECISION_REVIEW_THRESHOLD

        # Decision Logic:
        # 1. Any CRITICAL risk -> Automatic SKIP
        if critical_risks:
            recommendation = DecisionRecommendation.SKIP
            decision_factor = f"Rejected due to critical risk: {critical_risks[0].description}"
        # 2. Multiple must-have gaps (>= 3) or very low score -> SKIP
        elif len(must_have_gaps) >= 3 or score < review_thresh:
            recommendation = DecisionRecommendation.SKIP
            decision_factor = f"Score ({score:.1f}) is below minimum threshold ({review_thresh:.1f}) with {len(must_have_gaps)} must-have gaps."
        # 3. High score AND no High/Critical risks AND good must-have coverage -> APPLY
        elif score >= apply_thresh and len(high_risks) == 0 and len(must_have_gaps) <= 1:
            recommendation = DecisionRecommendation.APPLY
            decision_factor = f"Strong candidate-job fit ({score:.1f}/100) with verified technical alignment in {role_class.primary_role.value}."
        # 4. Moderate score or transferable cloud or experience gap -> REVIEW
        else:
            recommendation = DecisionRecommendation.REVIEW
            if cloud_eval.transferability_status == CloudTransferabilityStatus.TRANSFERABLE and "aws" in cloud_eval.cloud_requested.lower():
                decision_factor = f"Good technical match ({score:.1f}/100) with transferable GCP-to-AWS cloud gap."
            elif high_risks:
                decision_factor = f"Moderate fit ({score:.1f}/100) with flagged risk: {high_risks[0].description}"
            else:
                decision_factor = f"Moderate fit ({score:.1f}/100); recommended for human review."

        # Compile structured explainable reasoning
        work_dist_str = ", ".join(f"{k}: {v}%" for k, v in role_reality.work_distribution.items())
        reasoning_lines = [
            f"Recommendation: {recommendation.value} (Fit Score: {score:.1f}/100)",
            f"Key Factor: {decision_factor}",
            "",
            f"Role Reality: {role_class.primary_role.value} | Estimated Work Split: {work_dist_str}",
            f"Seniority: {role_class.seniority.value} (Candidate: 1.9+ verified years)",
            "",
            f"Verified Strengths: {', '.join(strengths[:8]) if strengths else 'None'}",
            f"Identified Gaps: {', '.join(gaps[:6]) if gaps else 'None'}",
            f"Cloud Status: {cloud_eval.transferability_status.value} ({cloud_eval.transferability_reasoning})",
        ]

        if risks:
            reasoning_lines.append("")
            reasoning_lines.append("Risk Assessment:")
            for r in risks[:3]:
                reasoning_lines.append(f"  - [{r.severity.value}] {r.description}")

        explainable_reasoning = "\n".join(reasoning_lines)

        from careerpilot.services.explanation_service import ExplanationService

        explanation_dict = ExplanationService.generate_job_explanation(
            jd=jd,
            matches=matches,
            role_class=role_class,
            cloud_eval=cloud_eval,
            fit_score=fit_score,
            recommendation=recommendation,
            risks=risks,
            candidate_profile=candidate_profile,
        )

        return JobAnalysisResult(
            job_id=jd.id,
            job_title=jd.job_title,
            company_name=jd.company_name,
            role_classification=role_class,
            role_reality=role_reality,
            seniority_detection=role_class.seniority if isinstance(role_class.seniority, SeniorityDetection) else SeniorityDetection(detected_seniority=role_class.seniority, reasoning=role_class.reasoning),
            cloud_transferability=cloud_eval,
            requirements=jd.requirements,
            matches=matches,
            fit_score=fit_score,
            recommendation=recommendation,
            risks=risks,
            key_strengths=strengths,
            key_gaps=gaps,
            transferable_skills=transferable_skills,
            explainable_reasoning=explainable_reasoning,
            decision_reason=explanation_dict["decision_reason"],
            next_action=explanation_dict["next_action"],
            confidence=explanation_dict.get("confidence", 0.95),
            top_matching_requirements=explanation_dict["top_matching_requirements"],
            missing_required_requirements=explanation_dict["missing_required_requirements"],
            missing_preferred_requirements=explanation_dict["missing_preferred_requirements"],
            experience_comparison=explanation_dict["experience_comparison"],
            cloud_comparison=explanation_dict["cloud_comparison"],
            zero_score_explanation=explanation_dict.get("zero_score_explanation"),
            penalty_details=explanation_dict.get("penalties", []),
        )

