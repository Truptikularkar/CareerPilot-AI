from typing import List, Dict, Any, Optional
from careerpilot.core.config import settings
from careerpilot.core.constants import (
    MatchStatus,
    RequirementImportance,
    TaxonomyCategory,
    CloudTransferabilityStatus,
    RoleCategory,
    SeniorityLevel,
)
from careerpilot.models.job import (
    JobDescription,
    RequirementMatch,
    CloudTransferability,
    RoleClassification,
    FitScoreBreakdown,
)
from careerpilot.models.candidate import CandidateProfile
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class CandidateJobFitScorer:
    """
    Computes an explainable, deterministic 9-component weighted fit score between a Job Description
    and verified Candidate Evidence. Enforces explicit penalties for experience shortfalls and missing must-haves.
    """

    @classmethod
    def compute_fit_score(
        cls,
        matches: List[RequirementMatch],
        role_class: RoleClassification,
        cloud_eval: CloudTransferability,
        preference_score: float,
        jd: JobDescription,
        candidate_profile: Optional[CandidateProfile] = None,
    ) -> FitScoreBreakdown:
        # 1. Must-Have Technical Skills Score
        must_haves = [m for m in matches if m.requirement.importance == RequirementImportance.MUST_HAVE]
        if not must_haves:
            must_haves = matches

        must_have_points = 0.0
        missing_must_have_count = 0
        for m in must_haves:
            if m.match_status == MatchStatus.MATCH:
                must_have_points += 100.0
            elif m.match_status == MatchStatus.PARTIAL:
                must_have_points += 55.0
            else:
                must_have_points += 0.0
                # Only technical/domain requirements count toward the heavy disqualifying gap penalty
                if m.requirement.category not in (TaxonomyCategory.SOFT_SKILL, TaxonomyCategory.OTHER):
                    missing_must_have_count += 1

        must_have_score = (must_have_points / len(must_haves)) if must_haves else 80.0

        # 2. Nice-to-Have Skills Score
        nice_to_haves = [m for m in matches if m.requirement.importance == RequirementImportance.NICE_TO_HAVE]
        if nice_to_haves:
            nth_points = 0.0
            for m in nice_to_haves:
                if m.match_status == MatchStatus.MATCH:
                    nth_points += 100.0
                elif m.match_status == MatchStatus.PARTIAL:
                    nth_points += 60.0
                else:
                    nth_points += 20.0
            nice_to_have_score = nth_points / len(nice_to_haves)
        else:
            nice_to_have_score = 85.0

        # 3. Experience Years Score (with material shortfall penalty)
        exp_matches = [m for m in matches if m.requirement.years_required]
        max_shortfall_years = 0.0

        if exp_matches:
            exp_points = 0.0
            for m in exp_matches:
                cand_yrs = m.candidate_years if m.candidate_years is not None else 1.9
                req_yrs = m.required_years or m.requirement.years_required or 0.0
                shortfall = req_yrs - cand_yrs
                if shortfall > 0:
                    max_shortfall_years = max(max_shortfall_years, shortfall)
                    if shortfall >= 2.0:
                        exp_points += 20.0  # Severe shortfall (e.g. 1.9 vs 4+ yrs)
                    elif shortfall >= 1.0:
                        exp_points += 40.0  # Substantial shortfall (e.g. 1.9 vs 3 yrs)
                    else:
                        exp_points += 65.0
                else:
                    exp_points += 100.0
            exp_score = exp_points / len(exp_matches)
        else:
            # Infer from seniority
            if role_class.seniority in (SeniorityLevel.ENTRY, SeniorityLevel.JUNIOR):
                exp_score = 100.0
            elif role_class.seniority == SeniorityLevel.MID:
                exp_score = 65.0
            elif role_class.seniority == SeniorityLevel.SENIOR:
                exp_score = 25.0
                max_shortfall_years = 3.0
            else:
                exp_score = 15.0
                max_shortfall_years = 5.0

        # 4. Role Taxonomy Alignment Score
        if role_class.primary_role in (
            RoleCategory.AI_DATA_ENGINEER,
            RoleCategory.DATA_ENGINEER,
            RoleCategory.GENAI_ENGINEER,
            RoleCategory.GCP_DATA_ENGINEER,
        ):
            role_score = 100.0
        elif role_class.primary_role in (RoleCategory.AI_ENGINEER, RoleCategory.CLOUD_DATA_ENGINEER):
            role_score = 85.0
        elif role_class.primary_role in (RoleCategory.ML_ENGINEER, RoleCategory.ANALYTICS_ENGINEER):
            role_score = 65.0
        elif role_class.primary_role == RoleCategory.DATA_SCIENTIST or "research" in jd.job_title.lower():
            role_score = 35.0
        else:
            role_score = 25.0

        # 5. Evidence Strength Score
        if matches:
            evid_count = sum(1 for m in matches if m.candidate_evidence_text or m.candidate_evidence_id)
            evidence_strength_score = max(35.0, min(100.0, (evid_count / len(matches)) * 100.0))
        else:
            evidence_strength_score = 80.0

        # 6. Location Preference Score
        loc_str = ((jd.location or "") + " " + jd.raw_text[:200]).lower()
        work_mode = (jd.work_mode or "").lower()

        # Build candidate's preferred and current locations
        candidate_locs = ["pune", "nagpur", "remote"]
        if candidate_profile:
            if candidate_profile.preferences and candidate_profile.preferences.target_locations:
                candidate_locs.extend([l.lower() for l in candidate_profile.preferences.target_locations])
            if candidate_profile.location:
                candidate_locs.append(candidate_profile.location.lower())

        if "remote" in loc_str or "remote" in work_mode:
            location_score = 100.0
        elif any(c in loc_str for c in candidate_locs if len(c) > 2):
            location_score = 100.0
        elif any(city in loc_str for city in ["pune", "nagpur", "bangalore", "bengaluru", "hyderabad", "mumbai", "delhi", "gurgaon", "noida"]):
            location_score = 85.0
        elif loc_str.strip():
            location_score = 65.0
        else:
            location_score = 90.0

        # 7. Company Preference Score
        comp_str = (jd.company_name or "").lower()
        if any(co in comp_str for co in ["google", "microsoft", "amazon", "meta", "apple", "nvidia", "databricks"]):
            company_score = 100.0
        elif preference_score > 0:
            company_score = min(100.0, max(60.0, preference_score))
        else:
            company_score = 85.0

        # 8. Cloud Transferability Score
        if cloud_eval.transferability_status == CloudTransferabilityStatus.MATCH:
            cloud_score = 100.0
        elif cloud_eval.transferability_status == CloudTransferabilityStatus.TRANSFERABLE:
            cloud_score = 75.0
        elif cloud_eval.transferability_status == CloudTransferabilityStatus.NOT_APPLICABLE:
            cloud_score = 85.0
        else:  # SIGNIFICANT_GAP
            cloud_score = 20.0

        # Backward compatibility scores
        has_genai_reqs = any("rag" in m.requirement.normalized_skill.lower() or "llm" in m.requirement.normalized_skill.lower() or "gemini" in m.requirement.normalized_skill.lower() for m in matches)
        genai_score = 100.0 if has_genai_reqs else (60.0 if "ai" in jd.job_title.lower() else 40.0)

        has_de_reqs = any(m.requirement.normalized_skill.lower() in ("python", "sql", "bigquery", "airflow", "data quality", "etl / elt pipelines") and m.match_status == MatchStatus.MATCH for m in matches)
        data_eng_score = 100.0 if has_de_reqs else (60.0 if "data" in jd.job_title.lower() else 35.0)

        # 9. Disqualifying Gap Penalties
        must_have_penalty = missing_must_have_count * settings.MUST_HAVE_PENALTY_PER_GAP

        experience_penalty = 0.0
        if max_shortfall_years >= 1.0:
            # Significant shortfall penalty (e.g. candidate has 1.9 yrs, JD requires 3+ yrs)
            experience_penalty = 15.0
        elif role_class.seniority in (SeniorityLevel.SENIOR, SeniorityLevel.LEAD):
            experience_penalty = 20.0

        disqualifying_gap_penalty = must_have_penalty + experience_penalty

        # Calibrated 9-Component Weights (Sum = 1.00)
        w_mh = 0.30
        w_nth = 0.05
        w_exp = 0.20
        w_role = 0.15
        w_evid = 0.10
        w_cloud = 0.10
        w_loc = 0.05
        w_comp = 0.05

        raw_weighted_total = (
            (must_have_score * w_mh)
            + (nice_to_have_score * w_nth)
            + (exp_score * w_exp)
            + (role_score * w_role)
            + (evidence_strength_score * w_evid)
            + (cloud_score * w_cloud)
            + (location_score * w_loc)
            + (company_score * w_comp)
        )

        final_score = max(0.0, min(100.0, raw_weighted_total - disqualifying_gap_penalty))

        weights_used = {
            "must_have": w_mh,
            "nice_to_have": w_nth,
            "experience": w_exp,
            "role_alignment": w_role,
            "evidence_strength": w_evid,
            "cloud_alignment": w_cloud,
            "location_preference": w_loc,
            "company_preference": w_comp,
        }

        explanation = (
            f"Calibrated 9-Component Fit Score: Must-Have ({must_have_score:.1f}/100), "
            f"Nice-To-Have ({nice_to_have_score:.1f}/100), Experience ({exp_score:.1f}/100), "
            f"Role ({role_score:.1f}/100), Evidence ({evidence_strength_score:.1f}/100), "
            f"Cloud ({cloud_score:.1f}/100), Location ({location_score:.1f}/100), "
            f"Company ({company_score:.1f}/100). "
            f"Disqualifying Gap Penalty: -{disqualifying_gap_penalty:.1f} pts "
            f"(Must-haves missing: {missing_must_have_count}, Exp shortfall: {max_shortfall_years:.1f}y)."
        )

        penalties_list = []
        if must_have_penalty > 0:
            penalties_list.append({
                "name": "Missing Required Skills",
                "deduction": round(must_have_penalty, 1),
                "reason": f"Deduction for {missing_must_have_count} missing must-have requirement(s)",
            })
        if experience_penalty > 0:
            penalties_list.append({
                "name": "Experience Level Gap",
                "deduction": round(experience_penalty, 1),
                "reason": f"Experience is below required level ({max_shortfall_years:.1f}y shortfall)",
            })

        return FitScoreBreakdown(
            must_have_score=round(must_have_score, 1),
            nice_to_have_score=round(nice_to_have_score, 1),
            experience_score=round(exp_score, 1),
            role_alignment_score=round(role_score, 1),
            evidence_strength_score=round(evidence_strength_score, 1),
            location_preference_score=round(location_score, 1),
            company_preference_score=round(company_score, 1),
            cloud_score=round(cloud_score, 1),
            disqualifying_gap_penalty=round(disqualifying_gap_penalty, 1),
            genai_score=round(genai_score, 1),
            data_eng_score=round(data_eng_score, 1),
            preference_score=round(company_score, 1),
            must_have_penalty=round(must_have_penalty, 1),
            total_weighted_score=round(final_score, 1),
            weights_used=weights_used,
            penalties=penalties_list,
            explanation=explanation,
        )

