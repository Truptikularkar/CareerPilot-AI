from typing import List
from careerpilot.core.constants import (
    RiskSeverity,
    RiskType,
    MatchStatus,
    RequirementImportance,
    CloudTransferabilityStatus,
    RoleCategory,
    SeniorityLevel,
)
from careerpilot.models.job import (
    JobDescription,
    RequirementMatch,
    CloudTransferability,
    RoleClassification,
    RiskItem,
)
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class RiskAnalyzer:
    """
    Identifies and assesses candidate application risks with explainable severities and mitigations.
    """

    @classmethod
    def analyze_risks(
        cls,
        matches: List[RequirementMatch],
        role_class: RoleClassification,
        cloud_eval: CloudTransferability,
        jd: JobDescription,
    ) -> List[RiskItem]:
        risks: List[RiskItem] = []

        # 1. Check for Critical Must-Have Skill Gaps
        must_have_gaps = [
            m for m in matches
            if m.requirement.importance == RequirementImportance.MUST_HAVE and m.match_status == MatchStatus.GAP
        ]
        if len(must_have_gaps) >= 3:
            risks.append(
                RiskItem(
                    risk_type=RiskType.MUST_HAVE_GAPS,
                    severity=RiskSeverity.CRITICAL,
                    description=f"Multiple critical must-have requirements missing ({len(must_have_gaps)} unevidenced skills: {', '.join(m.requirement.normalized_skill for m in must_have_gaps[:4])}).",
                    supporting_requirement="Must-Have Qualifications",
                    mitigation="Candidate should focus on roles closer to current verified stack before applying.",
                )
            )
        elif len(must_have_gaps) in (1, 2):
            for gap in must_have_gaps:
                risks.append(
                    RiskItem(
                        risk_type=RiskType.CRITICAL_SKILL_GAP,
                        severity=RiskSeverity.HIGH,
                        description=f"Must-have requirement '{gap.requirement.normalized_skill}' has no verified candidate evidence.",
                        supporting_requirement=gap.requirement.source_text,
                        mitigation="Highlight adjacent data engineering strengths in interview or clarify current self-study progress.",
                    )
                )

        # 2. Check for Cloud Mismatch
        if cloud_eval.transferability_status == CloudTransferabilityStatus.SIGNIFICANT_GAP:
            risks.append(
                RiskItem(
                    risk_type=RiskType.CLOUD_MISMATCH,
                    severity=RiskSeverity.HIGH,
                    description="Role heavily relies on deep proprietary AWS architecture (e.g. Glue, EMR, Redshift) where candidate only has verified GCP production experience.",
                    supporting_requirement=cloud_eval.cloud_requested,
                    candidate_evidence="GCP BigQuery, Cloud Storage, Vertex AI",
                    mitigation="Emphasize strong conceptual architectural parity between BigQuery/GCS and Redshift/S3 during interviews.",
                )
            )
        elif cloud_eval.transferability_status == CloudTransferabilityStatus.TRANSFERABLE and "aws" in cloud_eval.cloud_requested.lower():
            risks.append(
                RiskItem(
                    risk_type=RiskType.CLOUD_MISMATCH,
                    severity=RiskSeverity.LOW,
                    description="Role requests AWS experience; candidate's primary production cloud is GCP (transferable data pipeline concepts).",
                    supporting_requirement=cloud_eval.cloud_requested,
                    candidate_evidence="GCP production experience",
                    mitigation="Demonstrate fast transferability from GCP BigQuery and Airflow to AWS equivalents.",
                )
            )

        # 3. Check for Experience Shortfall & Seniority Mismatch
        for m in matches:
            if m.requirement.years_required and m.years_match == MatchStatus.GAP:
                risks.append(
                    RiskItem(
                        risk_type=RiskType.EXPERIENCE_SHORTFALL,
                        severity=RiskSeverity.HIGH if m.requirement.years_required >= 5.0 else RiskSeverity.MEDIUM,
                        description=f"Experience tenure gap: JD explicitly requires {m.requirement.years_required}+ years, candidate has 1.9+ verified years.",
                        supporting_requirement=m.requirement.source_text,
                        candidate_evidence="1.9+ years verified experience at Cognizant",
                        mitigation="Compensate with high-impact verified metrics (60% ticket automation, 35% data quality incident reduction).",
                    )
                )
                break  # Record one consolidated tenure gap

        if role_class.seniority in (SeniorityLevel.LEAD, SeniorityLevel.SENIOR) and not any(r.risk_type == RiskType.EXPERIENCE_SHORTFALL for r in risks):
            if role_class.seniority == SeniorityLevel.LEAD:
                risks.append(
                    RiskItem(
                        risk_type=RiskType.SENIORITY_MISMATCH,
                        severity=RiskSeverity.HIGH,
                        description=f"Role requires Lead/Architect seniority, exceeding candidate's 1.9+ years profile tenure.",
                        supporting_requirement=jd.job_title,
                        mitigation="Apply only if comfortable demonstrating independent system design ownership.",
                    )
                )

        # 4. Check for Research-Heavy or Role Mismatch
        if role_class.primary_role == RoleCategory.DATA_SCIENTIST and "research" in jd.raw_text.lower():
            risks.append(
                RiskItem(
                    risk_type=RiskType.RESEARCH_HEAVY,
                    severity=RiskSeverity.HIGH,
                    description="Role is heavily centered on academic/statistical research rather than production data and AI engineering.",
                    supporting_requirement=jd.job_title,
                    mitigation="Candidate preference strongly favors hands-on engineering implementation.",
                )
            )

        # 5. Check for Unsupported Tech (Mobile, Embedded, etc.)
        unsupported_terms = ["swift", "ios", "android", "flutter", "c++", "embedded", "firmware", "rust"]
        found_unsupported = [t for t in unsupported_terms if t in jd.raw_text.lower()]
        if found_unsupported:
            risks.append(
                RiskItem(
                    risk_type=RiskType.UNSUPPORTED_TECH,
                    severity=RiskSeverity.CRITICAL if len(found_unsupported) > 1 else RiskSeverity.HIGH,
                    description=f"JD requires technologies with zero candidate background: {', '.join(found_unsupported)}.",
                    supporting_requirement="Technical Requirements",
                    mitigation="Hard mismatch with candidate core profile.",
                )
            )

        return risks
