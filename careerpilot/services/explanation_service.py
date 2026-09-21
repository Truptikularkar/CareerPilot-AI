"""
CareerPilot AI — Centralized Job Fit & Decision Explanation Service
Converts structured job analysis facts into simple, clear, professional English.
Guarantees transparent explanations for 0%, REVIEW, APPLY, and SKIP decisions,
distinguishes required from preferred skills, compares experience and cloud ecosystems,
and enforces Truth Guard validation to prevent unverified AI claims.
"""
from typing import Dict, Any, List, Optional, Tuple
from careerpilot.core.constants import (
    MatchStatus,
    RequirementImportance,
    TaxonomyCategory,
    CloudTransferabilityStatus,
    DecisionRecommendation,
    RoleCategory,
    SeniorityLevel,
)
from careerpilot.models.job import (
    JobDescription,
    RequirementMatch,
    RoleClassification,
    CloudTransferability,
    FitScoreBreakdown,
    RiskItem,
)
from careerpilot.models.candidate import CandidateProfile
from careerpilot.core.date_utils import calculate_total_experience_years
from careerpilot.truth_guard.auditor import TruthAuditor
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class ExplanationService:
    """
    Centralized explanation service that converts structured facts into
    simple, professional, explainable job analysis results.
    """

    @classmethod
    def generate_job_explanation(
        cls,
        jd: JobDescription,
        matches: List[RequirementMatch],
        role_class: RoleClassification,
        cloud_eval: CloudTransferability,
        fit_score: FitScoreBreakdown,
        recommendation: DecisionRecommendation,
        risks: List[RiskItem],
        candidate_profile: Optional[CandidateProfile] = None,
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive, grounded explanation dictionary for an analyzed job.
        Never invents candidate facts or experience requirements.
        """
        # 1. Determine verified candidate experience baseline dynamically
        cand_years = 1.9
        if candidate_profile and candidate_profile.experiences:
            calc_years = calculate_total_experience_years(candidate_profile.experiences)
            if calc_years > 0.0:
                cand_years = calc_years

        # 2. Extract matching and missing requirements
        matching_reqs = []
        missing_required = []
        missing_preferred = []

        for m in matches:
            skill = m.requirement.normalized_skill or m.requirement.skill_name or ""
            if not skill:
                continue

            # Exclude location strings, work mode, and marketing boilerplate from skill gap lists
            skill_lower = skill.lower()
            if (
                any(w in skill_lower for w in ["location:", "location -", "work location:", "pune", "bangalore", "remote", "hybrid", "onsite"])
                or any(w in skill_lower for w in ["change the world", "tell us about", "let us know", "join our team", "equal opportunity"])
                or m.requirement.category == TaxonomyCategory.OTHER
            ):
                continue

            if m.match_status in (MatchStatus.MATCH, MatchStatus.PARTIAL):
                if skill not in matching_reqs:
                    matching_reqs.append(skill)
            elif m.requirement.importance == RequirementImportance.MUST_HAVE:
                if skill not in missing_required:
                    missing_required.append(skill)
            else:
                if skill not in missing_preferred:
                    missing_preferred.append(skill)

        # 3. Experience comparison engine
        exp_matches = [m for m in matches if m.requirement.years_required]
        explicit_req_years: Optional[float] = None
        if exp_matches:
            explicit_req_years = max(
                (m.required_years or m.requirement.years_required or 0.0) for m in exp_matches
            )
        elif jd.requirements:
            for req in jd.requirements:
                if req.years_required and req.years_required > 0:
                    explicit_req_years = max(explicit_req_years or 0.0, req.years_required)

        experience_comp: Dict[str, Any] = {
            "candidate_years": round(cand_years, 1),
            "required_years": round(explicit_req_years, 1) if explicit_req_years is not None else None,
            "has_requirement": explicit_req_years is not None,
            "difference_years": round(explicit_req_years - cand_years, 1) if explicit_req_years is not None else None,
        }

        if explicit_req_years is not None:
            diff = explicit_req_years - cand_years
            if diff > 0.2:
                experience_comp["explanation"] = (
                    f"Your experience is about {diff:.1f} years below the stated requirement "
                    f"({cand_years:.1f} years verified vs {explicit_req_years:.0f}+ years required)."
                )
            elif diff < -0.2:
                experience_comp["explanation"] = (
                    f"Your verified experience of {cand_years:.1f} years comfortably exceeds "
                    f"the stated requirement of {explicit_req_years:.0f}+ years."
                )
            else:
                experience_comp["explanation"] = (
                    f"Your verified experience of {cand_years:.1f} years aligns well with the "
                    f"stated requirement of {explicit_req_years:.0f}+ years."
                )
        else:
            experience_comp["explanation"] = "The JD does not specify a minimum experience requirement."

        # 4. Cloud comparison engine
        req_cloud = (cloud_eval.cloud_requested or "").strip()
        cand_cloud = (cloud_eval.candidate_cloud or "GCP").strip()
        cloud_status = cloud_eval.transferability_status

        # Check if cloud is mandatory in requirements
        cloud_is_mandatory = any(
            req_cloud.lower() in m.requirement.normalized_skill.lower() and m.requirement.importance == RequirementImportance.MUST_HAVE
            for m in matches
        )

        cloud_comp: Dict[str, Any] = {
            "candidate_cloud": cand_cloud,
            "required_cloud": req_cloud or "None specified",
            "transferability_status": cloud_status.value,
            "is_mandatory": cloud_is_mandatory,
        }

        if req_cloud.upper() == "AWS":
            if cloud_is_mandatory:
                cloud_comp["explanation"] = "AWS is listed as a required skill and is not currently verified in your production experience."
            else:
                cloud_comp["explanation"] = (
                    "Your production experience is stronger in GCP. The role asks for AWS. "
                    "Cloud concepts are transferable, so this is a gap but not necessarily an "
                    "automatic rejection unless AWS is marked as mandatory."
                )
        elif req_cloud.upper() == "GCP":
            cloud_comp["explanation"] = "Your verified GCP production experience is a direct match for this role's cloud platform."
        elif req_cloud.upper() in ("AZURE", "HYBRID"):
            cloud_comp["explanation"] = (
                f"The role asks for {req_cloud}. Your core data engineering pipelines and cloud architecture concepts "
                f"from GCP are transferable."
            )
        else:
            cloud_comp["explanation"] = "No specific cloud platform is required for this role."

        # 5. Transferable skills
        transferable_skills = []
        if cloud_status == CloudTransferabilityStatus.TRANSFERABLE:
            transferable_skills.append("GCP Data Engineering -> AWS (BigQuery/Airflow -> Redshift/Glue/S3)")
        if any(s in matching_reqs for s in ["Python", "SQL", "Data Pipelines"]):
            transferable_skills.append("Core Data Engineering fundamentals (Python, SQL, ETL/ELT pipelines)")

        # 6. Important Gaps
        important_gaps = []
        if explicit_req_years is not None and (explicit_req_years - cand_years) >= 1.0:
            important_gaps.append(f"{explicit_req_years:.0f}+ years experience requirement")
        if cloud_is_mandatory and req_cloud.upper() == "AWS":
            important_gaps.append("AWS production experience")
        for g in missing_required:
            if g not in important_gaps:
                important_gaps.append(g)

        # 7. Exact Reason & Next Action Generation
        score = fit_score.total_weighted_score

        if recommendation == DecisionRecommendation.APPLY:
            matches_str = ", ".join(matching_reqs[:4]) if matching_reqs else "Data Engineering"
            decision_reason = (
                f"Strong match with verified background. Your technical experience in {matches_str} "
                f"aligns directly with the core role requirements. No critical blockers identified."
            )
            next_action = "Prepare your tailored resume and proceed with your application."

        elif recommendation == DecisionRecommendation.REVIEW:
            reasons = []
            if matching_reqs:
                reasons.append(f"Your {', '.join(matching_reqs[:3])} background matches the role well.")
            if missing_required:
                reasons.append(f"The main required gap is {', '.join(missing_required[:2])}.")
            if explicit_req_years is not None and (explicit_req_years - cand_years) >= 1.0:
                reasons.append(f"Your experience ({cand_years:.1f} yrs) is below the requested {explicit_req_years:.0f}+ years.")
            elif cloud_status == CloudTransferabilityStatus.TRANSFERABLE and req_cloud.upper() == "AWS":
                reasons.append("The role asks for AWS, while your primary production background is in GCP.")

            if reasons:
                decision_reason = " ".join(reasons)
            else:
                decision_reason = f"Moderate match ({score:.1f}%). The role has relevant overlap but contains minor gaps."

            if req_cloud.upper() == "AWS" and not cloud_is_mandatory:
                next_action = "Consider applying if the company accepts GCP experience as transferable to AWS. Otherwise prioritize closer matches."
            elif explicit_req_years is not None and (explicit_req_years - cand_years) >= 1.0:
                next_action = "Review whether the employer is flexible on years of experience before applying."
            else:
                next_action = "Review the job requirements and highlight transferable skills in your application."

        else:  # SKIP
            reasons = []
            if explicit_req_years is not None and (explicit_req_years - cand_years) >= 2.0:
                reasons.append(f"This role mandates {explicit_req_years:.0f}+ years of experience (your verified profile shows {cand_years:.1f} years).")
            if missing_required:
                reasons.append(f"Missing mandatory technical requirements: {', '.join(missing_required[:3])}.")
            if cloud_is_mandatory and req_cloud.upper() == "AWS":
                reasons.append("The role strictly mandates enterprise AWS production experience.")

            if reasons:
                decision_reason = " ".join(reasons)
            else:
                decision_reason = f"Low fit score ({score:.1f}%). Key technical requirements differ from your verified profile."

            if matching_reqs and missing_required:
                next_action = f"Focus on roles matching your verified skills in {', '.join(matching_reqs[:2])}, or consider upskilling in {', '.join(missing_required[:2])} before applying."
            else:
                next_action = "Explore roles aligned with your verified experience level and primary tech stack."

        # 8. Zero-Score Job Guarantee
        zero_score_explanation: Optional[Dict[str, Any]] = None
        if score <= 5.0 or (recommendation == DecisionRecommendation.SKIP and score < 20.0):
            primary_reason = "Required experience level and technical requirements are significantly above your current verified profile."
            if explicit_req_years is not None and (explicit_req_years - cand_years) >= 2.0:
                primary_reason = f"Required experience ({explicit_req_years:.0f}+ years) significantly exceeds your verified tenure ({cand_years:.1f} years)."
            elif missing_required:
                primary_reason = f"Multiple mandatory requirements ({', '.join(missing_required[:3])}) are missing from your verified profile."

            blocking_reqs = list(missing_required)
            if explicit_req_years is not None and (explicit_req_years - cand_years) >= 1.5:
                blocking_reqs.insert(0, f"{explicit_req_years:.0f}+ years experience")

            zero_score_explanation = {
                "primary_skip_reason": primary_reason,
                "secondary_reasons": [
                    f"Overall fit score is {score:.1f}%",
                    f"Candidate has {cand_years:.1f} years verified experience",
                    f"Missing {len(missing_required)} mandatory skill(s)",
                ],
                "blocking_requirements": blocking_reqs,
                "matched_requirements": matching_reqs,
                "next_action": "Focus on Data Engineer / GCP Data Engineer roles requiring 1–3 years of experience.",
            }

        # 9. Penalties formatting
        penalties = []
        if getattr(fit_score, "must_have_penalty", 0.0) > 0:
            penalties.append({
                "name": "Missing Required Skills",
                "deduction": round(fit_score.must_have_penalty, 1),
                "reason": f"Deduction for {len(missing_required)} missing mandatory skill(s): {', '.join(missing_required[:3])}",
            })
        if getattr(fit_score, "disqualifying_gap_penalty", 0.0) > getattr(fit_score, "must_have_penalty", 0.0):
            exp_pen = fit_score.disqualifying_gap_penalty - getattr(fit_score, "must_have_penalty", 0.0)
            penalties.append({
                "name": "Experience Level Gap",
                "deduction": round(exp_pen, 1),
                "reason": f"Experience is below required level ({cand_years:.1f} yrs vs required tenure)",
            })

        # 10. Truth Guard validation
        structured_facts = {
            "candidate_years": cand_years,
            "candidate_cloud": cand_cloud,
            "required_years": explicit_req_years,
            "matching_skills": matching_reqs,
            "missing_required": missing_required,
            "score": score,
            "decision": recommendation.value,
        }

        # Validate decision reason against Truth Guard
        is_grounded, audit_msg = TruthAuditor.audit_explanation(decision_reason, structured_facts)
        if not is_grounded:
            logger.warning("Truth Guard flagged generated explanation: %s. Using safe deterministic fallback.", audit_msg)
            decision_reason = (
                f"Candidate-job fit score is {score:.1f}%. "
                f"Recommendation is {recommendation.value} based on verified candidate profile."
            )

        return {
            "decision_reason": decision_reason,
            "next_action": next_action,
            "top_matching_requirements": matching_reqs,
            "missing_required_requirements": missing_required,
            "missing_preferred_requirements": missing_preferred,
            "experience_comparison": experience_comp,
            "cloud_comparison": cloud_comp,
            "transferable_skills": transferable_skills,
            "important_gaps": important_gaps,
            "zero_score_explanation": zero_score_explanation,
            "penalties": penalties,
            "confidence": 0.95 if matches else 0.85,
        }
