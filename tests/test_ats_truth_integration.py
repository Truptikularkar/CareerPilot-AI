import pytest
from pathlib import Path
from careerpilot.core.constants import MatchLevel, TruthValidationStatus, SuggestionPriority
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.models.resume import TruthValidationReport, TruthClaimCheck, ClaimType


def test_ats_truth_integration_aws_gap_truthful():
    # JD requires AWS Redshift and S3, candidate only has GCP in production
    eval_file = Path("data/jobs/evaluation/05_aws_data_engineer_transferable.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)

    report = ATSEvaluator.evaluate_resume(resume, analysis)

    # Amazon Redshift must be flagged as a gap, but NOT recommended to fabricate
    redshift_item = next((m for m in report.coverage_matrix if "redshift" in m.requirement.lower()), None)
    if redshift_item:
        assert redshift_item.match_level == MatchLevel.GAP
        assert "No verified production" in redshift_item.candidate_evidence or "NOT_VERIFIED" in redshift_item.truth_status or "Truthfully omitted" in redshift_item.recommendation

    # Recommendations must never say "Add AWS as a skill" or "Add Redshift"
    for s in report.suggestions:
        if "redshift" in s.recommended_action.lower() or "aws" in s.recommended_action.lower() or "s3" in s.recommended_action.lower():
            assert "do not add" in s.recommended_action.lower() or "do not fabricate" in s.recommended_action.lower() or "transferable" in s.recommended_action.lower()




def test_ats_truth_integration_blocked_claim_penalized():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)

    # Simulate a truth violation on the resume
    resume.truth_report = TruthValidationReport(
        status=TruthValidationStatus.BLOCK,
        verified_claims_count=2,
        blocked_claims=[
            TruthClaimCheck(
                claim_text="Optimized BigQuery query costs by 40%",
                claim_type=ClaimType.METRIC,
                status=TruthValidationStatus.BLOCK,
                violation_reason="Unverified metric '40%' detected in text.",
            )
        ],
        summary_reasoning="Blocked due to unverified metric.",
    )

    report = ATSEvaluator.evaluate_resume(resume, analysis)
    assert report.truth_status == TruthValidationStatus.BLOCK
    assert report.truth_violations_count == 1
    # Check that a critical safety suggestion is emitted
    assert any(s.priority == SuggestionPriority.CRITICAL for s in report.suggestions)
    # Score should reflect severe penalty (< 70.0)
    assert report.overall_score < 70.0
