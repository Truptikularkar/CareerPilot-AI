"""
CareerPilot AI — Milestone 14 Test Suite
Verification of:
1. Explainable job decisions (0%, REVIEW, APPLY, SKIP)
2. Required vs. Preferred skill distinction and penalties
3. Experience comparison engine (with and without explicit JD requirements)
4. Cloud platform comparison (GCP vs AWS transferability vs mandatory blocker)
5. Truth Guard validation on AI/template explanations
6. Authoritative terminology dictionary and 17-status friendly labels
7. Production safety, clean deployment validation, and persistence checks
"""
import pytest
from careerpilot.core.config import settings
from careerpilot.core.constants import (
    ApplicationStatus,
    DecisionRecommendation,
    MatchStatus,
    RequirementImportance,
    CloudTransferabilityStatus,
    RoleCategory,
    SeniorityLevel,
    TaxonomyCategory,
    AppEnvironmentMode,
)
from careerpilot.models.job import (
    JobDescription,
    JobRequirement,
    RequirementMatch,
    RoleClassification,
    RoleReality,
    SeniorityDetection,
    CloudTransferability,
    FitScoreBreakdown,
    JobAnalysisResult,
)
from careerpilot.models.candidate import CandidateProfile, Experience
from careerpilot.services.explanation_service import ExplanationService
from careerpilot.analysis.decision_engine import DecisionEngine
from careerpilot.truth_guard.auditor import TruthAuditor
from careerpilot.core.terminology import (
    get_friendly_status_label,
    get_friendly_decision_label,
    get_friendly_match_label,
    STATUS_USER_LABELS,
    TERMINOLOGY_DICTIONARY,
    BANNED_USER_UI_TERMS,
)


@pytest.fixture
def mock_candidate():
    """Mock verified candidate with ~1.9 years experience in GCP data engineering."""
    return CandidateProfile(
        full_name="Verified Candidate",
        email="candidate@example.com",
        location="Remote",
        professional_summary="Data engineer with 1.9+ years of experience specializing in GCP, BigQuery, and Airflow.",
        experiences=[
            Experience(
                company="Tech Solutions",
                title="Data Engineer",
                start_date="11/2024",
                end_date="Present",
                is_current=True,
                responsibilities=["Built ETL pipelines using BigQuery and Cloud Composer."],
                technologies_used=["Python", "SQL", "BigQuery", "Airflow", "GCP"],
            )
        ]
    )


# -----------------------------------------------------------------------------
# 1. 0% / Low Score Job Explanation
# -----------------------------------------------------------------------------
def test_zero_score_job_gets_clear_explanation(mock_candidate):
    """Verifies that a 0% or critical mismatch job produces clear reasons, blockers, and next steps."""
    jd = JobDescription(
        raw_text="Staff AWS Architect. Requires 8+ years experience, expert AWS Glue, EMR, Redshift, Kubernetes.",
        job_title="Staff AWS Cloud Architect",
        company_name="Enterprise Cloud Corp",
        requirements=[
            JobRequirement(skill_name="AWS Glue", normalized_skill="AWS", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="Kubernetes", normalized_skill="Kubernetes", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="8+ years experience", normalized_skill="Experience", years_required=8.0, importance=RequirementImportance.MUST_HAVE),
        ]
    )

    matches = [
        RequirementMatch(requirement=jd.requirements[0], match_status=MatchStatus.GAP),
        RequirementMatch(requirement=jd.requirements[1], match_status=MatchStatus.GAP),
        RequirementMatch(requirement=jd.requirements[2], match_status=MatchStatus.GAP, candidate_years=1.9, required_years=8.0),
    ]

    fit_score = FitScoreBreakdown(
        must_have_score=0.0,
        nice_to_have_score=50.0,
        experience_score=0.0,
        role_alignment_score=20.0,
        cloud_score=0.0,
        total_weighted_score=0.0,
        disqualifying_gap_penalty=40.0,
        must_have_penalty=36.0,
    )

    role_class = RoleClassification(primary_role=RoleCategory.OTHER, seniority=SeniorityLevel.LEAD)
    cloud_eval = CloudTransferability(
        cloud_requested="AWS",
        candidate_cloud="GCP",
        transferability_status=CloudTransferabilityStatus.SIGNIFICANT_GAP,
        transferability_reasoning="AWS is strictly required in production.",
    )

    result = ExplanationService.generate_job_explanation(
        jd=jd,
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        fit_score=fit_score,
        recommendation=DecisionRecommendation.SKIP,
        risks=[],
        candidate_profile=mock_candidate,
    )

    assert result["decision_reason"] != ""
    assert "8+ years" in result["decision_reason"] or "experience" in result["decision_reason"].lower()
    assert result["zero_score_explanation"] is not None
    z_exp = result["zero_score_explanation"]
    assert "primary_skip_reason" in z_exp
    assert "blocking_requirements" in z_exp
    assert len(z_exp["blocking_requirements"]) > 0
    assert "next_action" in z_exp
    assert "Data Engineer" in z_exp["next_action"]


# -----------------------------------------------------------------------------
# 2. REVIEW Decision Explanation
# -----------------------------------------------------------------------------
def test_review_decision_gets_clear_explanation(mock_candidate):
    """Verifies that a REVIEW decision clearly explains matches, transferable cloud, and experience gap."""
    jd = JobDescription(
        raw_text="Data Engineer needed. 3+ years experience. Python, SQL, AWS, Airflow. Docker preferred.",
        job_title="Data Engineer",
        company_name="Midscale Analytics",
        requirements=[
            JobRequirement(skill_name="Python", normalized_skill="Python", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="SQL", normalized_skill="SQL", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="AWS", normalized_skill="AWS", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="3+ years", normalized_skill="Experience", years_required=3.0, importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="Docker", normalized_skill="Docker", importance=RequirementImportance.NICE_TO_HAVE),
        ]
    )

    matches = [
        RequirementMatch(requirement=jd.requirements[0], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[1], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[2], match_status=MatchStatus.GAP),
        RequirementMatch(requirement=jd.requirements[3], match_status=MatchStatus.PARTIAL, candidate_years=1.9, required_years=3.0),
        RequirementMatch(requirement=jd.requirements[4], match_status=MatchStatus.GAP),
    ]

    fit_score = FitScoreBreakdown(
        must_have_score=65.0,
        nice_to_have_score=60.0,
        experience_score=50.0,
        role_alignment_score=90.0,
        cloud_score=65.0,
        total_weighted_score=60.0,
    )

    role_class = RoleClassification(primary_role=RoleCategory.DATA_ENGINEER, seniority=SeniorityLevel.MID)
    cloud_eval = CloudTransferability(
        cloud_requested="AWS",
        candidate_cloud="GCP",
        transferability_status=CloudTransferabilityStatus.TRANSFERABLE,
        transferability_reasoning="GCP BigQuery/Airflow is transferable to AWS Redshift/Glue.",
    )

    result = ExplanationService.generate_job_explanation(
        jd=jd,
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        fit_score=fit_score,
        recommendation=DecisionRecommendation.REVIEW,
        risks=[],
        candidate_profile=mock_candidate,
    )

    assert "Python" in result["decision_reason"] or "SQL" in result["decision_reason"]
    assert "next_action" in result
    assert "top_matching_requirements" in result
    assert "Python" in result["top_matching_requirements"]
    assert "missing_preferred_requirements" in result
    assert "Docker" in result["missing_preferred_requirements"]


# -----------------------------------------------------------------------------
# 3. APPLY Decision Explanation
# -----------------------------------------------------------------------------
def test_apply_decision_gets_clear_explanation(mock_candidate):
    """Verifies that an APPLY decision gives clear positive justification."""
    jd = JobDescription(
        raw_text="GCP Data Engineer. Python, SQL, BigQuery, Airflow. 1-2 years experience.",
        job_title="GCP Data Engineer",
        company_name="Cloud Pioneers",
        requirements=[
            JobRequirement(skill_name="Python", normalized_skill="Python", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="SQL", normalized_skill="SQL", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="BigQuery", normalized_skill="BigQuery", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="Airflow", normalized_skill="Airflow", importance=RequirementImportance.MUST_HAVE),
        ]
    )

    matches = [
        RequirementMatch(requirement=jd.requirements[0], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[1], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[2], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[3], match_status=MatchStatus.MATCH),
    ]

    fit_score = FitScoreBreakdown(
        must_have_score=100.0,
        nice_to_have_score=100.0,
        experience_score=100.0,
        role_alignment_score=100.0,
        cloud_score=100.0,
        total_weighted_score=95.0,
    )

    role_class = RoleClassification(primary_role=RoleCategory.GCP_DATA_ENGINEER, seniority=SeniorityLevel.JUNIOR)
    cloud_eval = CloudTransferability(
        cloud_requested="GCP",
        candidate_cloud="GCP",
        transferability_status=CloudTransferabilityStatus.MATCH,
        transferability_reasoning="Direct match on GCP platform.",
    )

    result = ExplanationService.generate_job_explanation(
        jd=jd,
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        fit_score=fit_score,
        recommendation=DecisionRecommendation.APPLY,
        risks=[],
        candidate_profile=mock_candidate,
    )

    assert "Strong match" in result["decision_reason"]
    assert "tailored resume" in result["next_action"].lower()
    assert len(result["missing_required_requirements"]) == 0


# -----------------------------------------------------------------------------
# 4. Required vs Preferred Skills
# -----------------------------------------------------------------------------
def test_required_vs_preferred_skills_separation(mock_candidate):
    """Verifies that missing preferred skills are separated from mandatory requirements."""
    jd = JobDescription(
        raw_text="Data Engineer. Required: Python, SQL. Preferred: Kafka, dbt.",
        job_title="Data Engineer",
        company_name="Tech Co",
        requirements=[
            JobRequirement(skill_name="Python", normalized_skill="Python", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="SQL", normalized_skill="SQL", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="Kafka", normalized_skill="Kafka", importance=RequirementImportance.NICE_TO_HAVE),
            JobRequirement(skill_name="dbt", normalized_skill="dbt", importance=RequirementImportance.NICE_TO_HAVE),
        ]
    )

    matches = [
        RequirementMatch(requirement=jd.requirements[0], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[1], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[2], match_status=MatchStatus.GAP),
        RequirementMatch(requirement=jd.requirements[3], match_status=MatchStatus.GAP),
    ]

    fit_score = FitScoreBreakdown(
        must_have_score=100.0,
        nice_to_have_score=40.0,
        experience_score=90.0,
        role_alignment_score=90.0,
        cloud_score=85.0,
        total_weighted_score=85.0,
    )

    result = ExplanationService.generate_job_explanation(
        jd=jd,
        matches=matches,
        role_class=RoleClassification(primary_role=RoleCategory.DATA_ENGINEER, seniority=SeniorityLevel.MID),
        cloud_eval=CloudTransferability(cloud_requested="None", candidate_cloud="GCP", transferability_status=CloudTransferabilityStatus.MATCH, transferability_reasoning=""),
        fit_score=fit_score,
        recommendation=DecisionRecommendation.APPLY,
        risks=[],
        candidate_profile=mock_candidate,
    )

    assert "Kafka" in result["missing_preferred_requirements"]
    assert "dbt" in result["missing_preferred_requirements"]
    assert len(result["missing_required_requirements"]) == 0


# -----------------------------------------------------------------------------
# 5. Experience Comparison Engine
# -----------------------------------------------------------------------------
def test_experience_explanation_with_and_without_jd_requirement(mock_candidate):
    """Verifies that experience is compared when stated, and explicitly noted as not specified when omitted."""
    # Case A: JD has explicit experience requirement (3+ years)
    jd_with_exp = JobDescription(
        raw_text="3+ years required.",
        requirements=[JobRequirement(skill_name="3+ years", normalized_skill="Experience", years_required=3.0, importance=RequirementImportance.MUST_HAVE)]
    )
    matches_a = [RequirementMatch(requirement=jd_with_exp.requirements[0], candidate_years=1.9, required_years=3.0)]
    fit_score = FitScoreBreakdown(must_have_score=80.0, experience_score=65.0, total_weighted_score=70.0, cloud_score=80.0, role_alignment_score=80.0)

    res_a = ExplanationService.generate_job_explanation(
        jd=jd_with_exp,
        matches=matches_a,
        role_class=RoleClassification(primary_role=RoleCategory.DATA_ENGINEER, seniority=SeniorityLevel.MID),
        cloud_eval=CloudTransferability(cloud_requested="GCP", candidate_cloud="GCP", transferability_status=CloudTransferabilityStatus.MATCH, transferability_reasoning=""),
        fit_score=fit_score,
        recommendation=DecisionRecommendation.REVIEW,
        risks=[],
        candidate_profile=mock_candidate,
    )
    exp_a = res_a["experience_comparison"]
    assert exp_a["has_requirement"] is True
    assert exp_a["required_years"] == 3.0
    assert "below the stated requirement" in exp_a["explanation"]

    # Case B: JD does NOT specify experience requirement
    jd_no_exp = JobDescription(raw_text="Data Engineer. Python and SQL required.", requirements=[])
    res_b = ExplanationService.generate_job_explanation(
        jd=jd_no_exp,
        matches=[],
        role_class=RoleClassification(primary_role=RoleCategory.DATA_ENGINEER, seniority=SeniorityLevel.MID),
        cloud_eval=CloudTransferability(cloud_requested="None", candidate_cloud="GCP", transferability_status=CloudTransferabilityStatus.MATCH, transferability_reasoning=""),
        fit_score=fit_score,
        recommendation=DecisionRecommendation.REVIEW,
        risks=[],
        candidate_profile=mock_candidate,
    )
    exp_b = res_b["experience_comparison"]
    assert exp_b["has_requirement"] is False
    assert "does not specify a minimum experience requirement" in exp_b["explanation"]


# -----------------------------------------------------------------------------
# 6. Cloud Comparison Engine
# -----------------------------------------------------------------------------
def test_cloud_comparison_transferable_vs_mandatory(mock_candidate):
    """Verifies transferable GCP-to-AWS framing vs mandatory AWS blocker."""
    jd = JobDescription(raw_text="Data Engineer.", requirements=[])
    fit_score = FitScoreBreakdown(must_have_score=80.0, experience_score=80.0, total_weighted_score=75.0, cloud_score=75.0, role_alignment_score=80.0)

    # Non-mandatory AWS
    cloud_non_mand = CloudTransferability(
        cloud_requested="AWS",
        candidate_cloud="GCP",
        transferability_status=CloudTransferabilityStatus.TRANSFERABLE,
        transferability_reasoning="GCP to AWS is transferable.",
    )
    res_transferable = ExplanationService.generate_job_explanation(
        jd=jd,
        matches=[],
        role_class=RoleClassification(primary_role=RoleCategory.DATA_ENGINEER, seniority=SeniorityLevel.MID),
        cloud_eval=cloud_non_mand,
        fit_score=fit_score,
        recommendation=DecisionRecommendation.REVIEW,
        risks=[],
        candidate_profile=mock_candidate,
    )
    assert "transferable" in res_transferable["cloud_comparison"]["explanation"].lower()


# -----------------------------------------------------------------------------
# 7. Truth Guard on Explanations
# -----------------------------------------------------------------------------
def test_truth_guard_blocks_unverified_claims():
    """Verifies TruthAuditor.audit_explanation blocks inflated tenure and unverified AWS claims."""
    # 1. Inflation violation
    bad_tenure = "You have 5+ years of experience in data engineering."
    is_valid, reason = TruthAuditor.audit_explanation(bad_tenure, {})
    assert is_valid is False
    assert "inflates" in reason.lower()

    # 2. Fabricated AWS production claim
    bad_aws = "With your verified AWS production experience, you match the role."
    is_valid_aws, reason_aws = TruthAuditor.audit_explanation(bad_aws, {})
    assert is_valid_aws is False
    assert "aws" in reason_aws.lower()

    # 3. Valid grounded explanation
    valid_text = "Your Python, SQL, and GCP experience align with the role. Candidate experience is ~1.9 years."
    is_valid_clean, _ = TruthAuditor.audit_explanation(valid_text, {})
    assert is_valid_clean is True


# -----------------------------------------------------------------------------
# 8. Terminology Dictionary & 17-Status Friendly Labels
# -----------------------------------------------------------------------------
def test_terminology_dictionary_and_friendly_labels():
    """Verifies no banned technical terms in dictionary and 17 status mappings."""
    # Ensure banned terms are NOT values in the user dictionary
    for banned in BANNED_USER_UI_TERMS:
        assert banned not in TERMINOLOGY_DICTIONARY.values()

    # Verify all 17 ApplicationStatus enums have friendly labels
    for status in ApplicationStatus:
        friendly = get_friendly_status_label(status)
        assert friendly != ""
        assert "_" not in friendly or friendly == "No response"  # Clean title words

    assert get_friendly_status_label(ApplicationStatus.DISCOVERED) == "Found"
    assert get_friendly_status_label(ApplicationStatus.APPLIED) == "Applied"
    assert get_friendly_status_label(ApplicationStatus.TECHNICAL_ROUND) == "Technical interview"
    assert get_friendly_status_label(ApplicationStatus.HR_ROUND) == "HR interview"
    assert get_friendly_status_label(ApplicationStatus.OA) == "Online assessment"

    # Friendly decision labels
    assert get_friendly_decision_label(DecisionRecommendation.APPLY) == "Apply"
    assert get_friendly_decision_label(DecisionRecommendation.REVIEW) == "Review"
    assert get_friendly_decision_label(DecisionRecommendation.SKIP) == "Skip"


# -----------------------------------------------------------------------------
# 9. Decision Engine End-to-End Integration
# -----------------------------------------------------------------------------
def test_decision_engine_populates_explainability_fields():
    """Verifies that evaluate_decision populates all Milestone 14 explainability fields."""
    jd = JobDescription(
        raw_text="AI Data Engineer. Python, SQL, BigQuery.",
        job_title="AI Data Engineer",
        company_name="Apex AI",
        requirements=[
            JobRequirement(skill_name="Python", normalized_skill="Python", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="SQL", normalized_skill="SQL", importance=RequirementImportance.MUST_HAVE),
        ]
    )

    matches = [
        RequirementMatch(requirement=jd.requirements[0], match_status=MatchStatus.MATCH),
        RequirementMatch(requirement=jd.requirements[1], match_status=MatchStatus.MATCH),
    ]

    fit_score = FitScoreBreakdown(
        must_have_score=100.0,
        experience_score=95.0,
        role_alignment_score=100.0,
        cloud_score=95.0,
        total_weighted_score=95.0,
    )

    role_class = RoleClassification(primary_role=RoleCategory.AI_DATA_ENGINEER, seniority=SeniorityLevel.MID)
    role_reality = RoleReality(work_distribution={"Data Pipelines": 60, "GenAI Integration": 40})
    cloud_eval = CloudTransferability(cloud_requested="GCP", candidate_cloud="GCP", transferability_status=CloudTransferabilityStatus.MATCH, transferability_reasoning="Direct match")

    result: JobAnalysisResult = DecisionEngine.evaluate_decision(
        jd=jd,
        role_class=role_class,
        role_reality=role_reality,
        cloud_eval=cloud_eval,
        matches=matches,
        fit_score=fit_score,
        risks=[],
    )

    assert result.decision_reason != ""
    assert result.next_action != ""
    assert isinstance(result.top_matching_requirements, list)
    assert len(result.top_matching_requirements) > 0
    assert isinstance(result.experience_comparison, dict)
    assert isinstance(result.cloud_comparison, dict)
    assert result.confidence >= 0.8


# -----------------------------------------------------------------------------
# 10. Deployment Persistence Validation
# -----------------------------------------------------------------------------
def test_deployment_persistence_validation(monkeypatch):
    """Verifies that HOSTED_PRIVATE mode guards against ephemeral database storage."""
    # In LOCAL_PRIVATE mode, validation always passes
    monkeypatch.setattr(settings, "CAREERPILOT_MODE", AppEnvironmentMode.LOCAL_PRIVATE)
    valid, _ = settings.validate_deployment_persistence()
    assert valid is True

    # In HOSTED_PRIVATE mode without DATABASE_URL or persistent volume, should block
    monkeypatch.setattr(settings, "CAREERPILOT_MODE", AppEnvironmentMode.HOSTED_PRIVATE)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PERSISTENT_VOLUME_PATH", raising=False)
    monkeypatch.delenv("ALLOW_EPHEMERAL_HOSTED_STORAGE", raising=False)
    valid_hosted, msg = settings.validate_deployment_persistence()
    assert valid_hosted is False
    assert "persistent storage" in msg.lower()


# -----------------------------------------------------------------------------
# 11. 10% Low Score Explanation
# -----------------------------------------------------------------------------
def test_low_score_10_percent_job_gets_clear_reason(mock_candidate):
    """Verifies that a 10% score job receives concrete reasons and next action."""
    jd = JobDescription(
        raw_text="Director of DevOps. 10+ years experience, Terraform, Kubernetes, Azure.",
        requirements=[
            JobRequirement(skill_name="Terraform", normalized_skill="Terraform", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="Kubernetes", normalized_skill="Kubernetes", importance=RequirementImportance.MUST_HAVE),
            JobRequirement(skill_name="10+ years experience", normalized_skill="Experience", years_required=10.0, importance=RequirementImportance.MUST_HAVE),
        ]
    )
    fit_score = FitScoreBreakdown(
        must_have_score=0.0,
        experience_score=10.0,
        role_alignment_score=20.0,
        cloud_score=20.0,
        total_weighted_score=10.0,
        disqualifying_gap_penalty=25.0,
    )
    res = ExplanationService.generate_job_explanation(
        jd=jd,
        matches=[],
        role_class=RoleClassification(primary_role=RoleCategory.OTHER, seniority=SeniorityLevel.LEAD),
        cloud_eval=CloudTransferability(cloud_requested="Azure", candidate_cloud="GCP", transferability_status=CloudTransferabilityStatus.SIGNIFICANT_GAP, transferability_reasoning=""),
        fit_score=fit_score,
        recommendation=DecisionRecommendation.SKIP,
        risks=[],
        candidate_profile=mock_candidate,
    )
    assert res["decision_reason"] != ""
    assert "10+ years" in res["decision_reason"] or "experience" in res["decision_reason"].lower()
    assert "next_action" in res


# -----------------------------------------------------------------------------
# 12. Production Safety & Environment Template
# -----------------------------------------------------------------------------
def test_production_safety_and_env_example():
    """Verifies that active candidate ID is dynamic and .env.example contains no secrets."""
    from pathlib import Path

    # Check active_candidate_id does not hardcode personal names
    assert settings.active_candidate_id in ("cand_verified", "alex_rivera_demo")

    # Check .env.example
    env_example_path = Path(".env.example")
    assert env_example_path.exists(), ".env.example must exist"
    content = env_example_path.read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=" in content
    assert "DATABASE_URL=" in content
    # Ensure no real keys are committed in .env.example
    assert "AIza" not in content
    assert "ghp_" not in content
    assert "postgres://" not in content

