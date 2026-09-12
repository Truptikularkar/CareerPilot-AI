"""
CareerPilot AI — Authoritative User-Facing Terminology Dictionary
Provides standardized, human-friendly professional wording for UI display,
replacing internal developer/engineering jargon, and mapping 17-stage recruitment
lifecycle statuses and match statuses to intuitive labels.
"""
from typing import Dict, Any, Optional
from careerpilot.core.constants import ApplicationStatus, MatchStatus, DecisionRecommendation

# Master Terminology Mapping (Internal Jargon -> User-Facing Professional English)
TERMINOLOGY_DICTIONARY: Dict[str, str] = {
    "composite_alignment_score": "Fit Score",
    "composite_score": "Fit Score",
    "overall_fit": "Fit Score",
    "alignment_rationale": "Why this job matches",
    "explainable_reasoning": "Why this job matches",
    "capability_deficiencies": "Missing required skills",
    "must_have_gaps": "Missing required skills",
    "seniority_shortfall_penalty": "Experience gap",
    "experience_shortfall": "Experience gap",
    "secondary_competencies": "Preferred skills",
    "nice_to_have_skills": "Preferred skills",
    "candidate_competency_vectors": "Your strengths",
    "verified_strengths": "Your strengths",
    "key_strengths": "Your strengths",
    "recommended_trajectory_intervention": "Next step",
    "recommendation": "Recommendation",
    "next_action": "Next step",
    "semantic_keyword_alignment": "JD keyword match",
    "coverage_deficit": "Missing important keywords",
    "disqualifying_gap_penalty": "Penalty deductions",
    "role_reality": "Role breakdown",
    "cloud_transferability": "Cloud environment match",
    "retrieval_confidence": "Evidence match",
}

# 17-Status Application Recruitment Lifecycle Friendly Labels
STATUS_USER_LABELS: Dict[ApplicationStatus, str] = {
    ApplicationStatus.DISCOVERED: "Found",
    ApplicationStatus.ANALYZED: "Analyzed",
    ApplicationStatus.SAVED: "Saved",
    ApplicationStatus.APPLIED: "Applied",
    ApplicationStatus.ACKNOWLEDGED: "Employer responded",
    ApplicationStatus.SCREENING: "Screening",
    ApplicationStatus.OA: "Online assessment",
    ApplicationStatus.INTERVIEWING: "Interviewing",
    ApplicationStatus.TECHNICAL_ROUND: "Technical interview",
    ApplicationStatus.HR_ROUND: "HR interview",
    ApplicationStatus.FINAL_ROUND: "Final interview",
    ApplicationStatus.OFFER: "Offer",
    ApplicationStatus.ACCEPTED: "Accepted",
    ApplicationStatus.REJECTED: "Rejected",
    ApplicationStatus.WITHDRAWN: "Withdrawn",
    ApplicationStatus.ON_HOLD: "On hold",
    ApplicationStatus.NO_RESPONSE: "No response",
}

# Match Status Friendly Labels & Badges
MATCH_STATUS_LABELS: Dict[MatchStatus, str] = {
    MatchStatus.MATCH: "Match",
    MatchStatus.PARTIAL: "Partial Match",
    MatchStatus.GAP: "Missing",
}

MATCH_STATUS_EXTENDED_LABELS: Dict[str, str] = {
    "MATCH": "Match",
    "PARTIAL": "Partial Match",
    "MISSING": "Missing",
    "NOT_VERIFIED": "Not Verified",
    "NOT_APPLICABLE": "Not Applicable",
}

# Banned AI / Engineering Jargon in Normal User Views
BANNED_USER_UI_TERMS = [
    "semantic alignment",
    "multidimensional fit",
    "competency vector",
    "retrieval confidence",
    "evidence graph",
    "latent similarity",
    "inference pipeline",
    "orchestration state",
    "embedding relevance",
    "seniority shortfall penalty",
    "capability deficiencies",
    "recommended trajectory intervention",
]


def get_friendly_status_label(status: Any) -> str:
    """Returns clean, human-friendly label for any ApplicationStatus enum or string."""
    if isinstance(status, ApplicationStatus):
        return STATUS_USER_LABELS.get(status, status.value.replace("_", " ").title())
    if isinstance(status, str):
        try:
            enum_val = ApplicationStatus(status)
            return STATUS_USER_LABELS.get(enum_val, status.replace("_", " ").title())
        except Exception:
            # Check if string matches any key or name
            clean_str = status.upper().replace(" ", "_")
            for k, v in STATUS_USER_LABELS.items():
                if k.value == clean_str or k.name == clean_str:
                    return v
            return status.replace("_", " ").title()
    return str(status)


def get_friendly_decision_label(rec: Any) -> str:
    """Returns friendly label and emoji for system recommendations."""
    if isinstance(rec, DecisionRecommendation):
        val = rec.value
    else:
        val = str(rec).upper()

    if val == "APPLY":
        return "Apply"
    elif val == "REVIEW":
        return "Review"
    elif val == "SKIP":
        return "Skip"
    return val.title()


def get_friendly_match_label(status: Any) -> str:
    """Returns clean user-facing match status."""
    if isinstance(status, MatchStatus):
        return MATCH_STATUS_LABELS.get(status, status.value)
    if isinstance(status, str):
        status_upper = status.upper()
        if status_upper in MATCH_STATUS_EXTENDED_LABELS:
            return MATCH_STATUS_EXTENDED_LABELS[status_upper]
        if status_upper == "GAP":
            return "Missing"
    return str(status).replace("_", " ").title()
