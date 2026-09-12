import pytest
from careerpilot.core.constants import TruthValidationStatus, QuestionCategory
from careerpilot.models.interview import InterviewAnswer, STARAnswer
from careerpilot.interview.truth_validator import InterviewTruthValidator
from careerpilot.interview.gap_handler import GapHandler
from careerpilot.models.ats import InterviewReadinessSeed
from careerpilot.graphs.job_analysis_graph import analyze_job
from pathlib import Path


def test_interview_truth_guard_pass_grounded_answers():
    answers = [
        InterviewAnswer(
            answer_id="a_test_pass",
            question_id="q_test_pass",
            direct_answer="I optimized BigQuery queries using partitioning and clustering.",
            explanation="Partitioning filters date blocks while clustering sorts keys.",
            candidate_example="At Cognizant, I applied this across tables ingesting ~500k+ daily records.",
            technical_details="Monitored Information Schema scanned bytes.",
            result_impact="Achieved a verified ~25% reduction in BigQuery costs.",
            possible_followup="Can explain clustering key cardinality.",
            short_version="Optimized BigQuery reducing costs by ~25%.",
            standard_version="Optimized BigQuery reducing costs by ~25%.",
            detailed_version="Optimized BigQuery reducing costs by ~25%.",
            grounded_evidence_ids=["EXP_COGNIZANT_005"],
            evidence_status="VERIFIED",
        )
    ]

    report = InterviewTruthValidator.validate_interview_answers(answers, [])
    assert report.status == TruthValidationStatus.PASS
    assert len(report.blocked_claims) == 0


def test_interview_truth_guard_negative_aws_production_claim():
    answers = [
        InterviewAnswer(
            answer_id="a_test_bad_aws",
            question_id="q_test_bad_aws",
            direct_answer="I served as Lead AWS Data Engineer in production managing AWS Glue and Redshift pipelines.",
            explanation="Managed multi-terabyte AWS production data warehouses.",
            candidate_example="Deployed AWS production pipelines at Cognizant.",
            technical_details="AWS Glue jobs.",
            result_impact="Improved AWS pipeline performance.",
            possible_followup="",
            grounded_evidence_ids=[],
            evidence_status="VERIFIED",
        )
    ]

    report = InterviewTruthValidator.validate_interview_answers(answers, [])
    assert report.status == TruthValidationStatus.BLOCK
    assert any("AWS production" in c.violation_reason for c in report.blocked_claims)


def test_interview_truth_guard_negative_inflated_metric():
    answers = [
        InterviewAnswer(
            answer_id="a_test_bad_metric",
            question_id="q_test_bad_metric",
            direct_answer="I optimized BigQuery queries to reduce query costs by 45%.",
            explanation="Tuned queries.",
            candidate_example="Cognizant data warehouse.",
            technical_details="",
            result_impact="Reduced costs by 45%.",
            possible_followup="",
            grounded_evidence_ids=[],
            evidence_status="VERIFIED",
        )
    ]

    report = InterviewTruthValidator.validate_interview_answers(answers, [])
    assert report.status == TruthValidationStatus.BLOCK
    assert any("Unverified metric" in c.violation_reason for c in report.blocked_claims)


def test_interview_gap_handler_transferable_framing():
    eval_file = Path("data/jobs/evaluation/05_aws_data_engineer_transferable.txt")
    analysis = analyze_job(eval_file)
    seed = InterviewReadinessSeed(
        job_id="job_aws",
        target_role="Data Engineer",
        high_priority_skills=["Python", "SQL", "Airflow"],
        candidate_strengths=["BigQuery", "GCP"],
        candidate_gaps=["Amazon Web Services (AWS)", "Amazon Redshift"],
    )

    questions, answers = GapHandler.generate_gap_questions_and_answers(analysis, seed)

    assert len(questions) >= 1
    assert len(answers) >= 1

    aws_ans = next((a for a in answers if "aws" in a.direct_answer.lower() or "gcp" in a.direct_answer.lower()), None)
    assert aws_ans is not None
    # Must explicitly state GCP background and transferable concepts, NOT claim AWS production
    assert "Google Cloud Platform" in aws_ans.direct_answer or "GCP" in aws_ans.direct_answer
    assert "transferable" in aws_ans.direct_answer.lower() or "transferable" in aws_ans.explanation.lower()
    assert aws_ans.evidence_status == "TRANSFERABLE"
