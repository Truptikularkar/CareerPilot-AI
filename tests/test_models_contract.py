import pytest
import json
from careerpilot.models.candidate import CandidateProfile, Skill, Experience, Project, Education
from careerpilot.models.evidence import CandidateEvidence
from careerpilot.models.job import (
    JobDescription,
    JobRequirement,
    SeniorityDetection,
    RoleClassification,
    CloudTransferability,
    JobAnalysisResult,
    FitScoreBreakdown,
    RiskItem,
)
from careerpilot.models.resume import (
    TailoredResume,
    ResumeStrategy,
    ResumeSummary,
    ResumeExperienceEntry,
    ResumeProjectEntry,
    TruthValidationReport,
    TruthClaimCheck,
)
from careerpilot.models.ats import ATSReport, ATSScoreComponent
from careerpilot.models.interview import InterviewQuestion, InterviewAnswer, PreparationRoadmap, PreparationDayPlan
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation, FinalInterviewReport
from careerpilot.core.constants import (
    SkillCategory,
    SeniorityLevel,
    RoleCategory,
    RequirementImportance,
    ResumeStrategyType,
    TruthValidationStatus,
    ClaimType,
    QuestionCategory,
    DifficultyLevel,
    QuestionPriority,
    MockInterviewMode,
    InterviewerPersona,
    EvidenceType,
    EvidenceStatus,
    RiskType,
    RiskSeverity,
)


def test_candidate_profile_serialization_round_trip():
    profile = CandidateProfile(
        full_name="Trupti Kularkar",
        email="kularkartrupti@gmail.com",
        professional_summary="AI Data Engineer with 1.9+ years GCP experience.",
        skills=[Skill(name="Python", category=SkillCategory.PROGRAMMING)],
        experiences=[Experience(company="Cognizant", title="Programmer Analyst", start_date="2023")],
    )
    dumped = profile.model_dump()
    json_str = json.dumps(dumped)
    loaded = CandidateProfile.model_validate(json.loads(json_str))
    assert loaded.full_name == "Trupti Kularkar"
    assert len(loaded.skills) == 1
    assert loaded.skills[0].name == "Python"


def test_job_analysis_contract_and_properties():
    sen = SeniorityDetection(detected_seniority=SeniorityLevel.MID, explicit_years_required=2.0)
    assert sen.detected_seniority == SeniorityLevel.MID
    assert sen.estimated_level == SeniorityLevel.MID

    cloud = CloudTransferability(
        cloud_requested="AWS",
        candidate_cloud="GCP",
        transferability_reasoning="BigQuery maps to Redshift",
    )
    assert cloud.primary_target_cloud == "AWS"
    assert cloud.candidate_verified_cloud == "GCP"
    assert cloud.explanation == "BigQuery maps to Redshift"

    risk = RiskItem(
        risk_type=RiskType.EXPERIENCE_SHORTFALL,
        severity=RiskSeverity.LOW,
        description="Minor experience shortfall",
    )
    assert risk.title == "Experience Shortfall"

    fit = FitScoreBreakdown(
        must_have_score=90.0,
        experience_score=85.0,
        role_alignment_score=95.0,
        genai_score=90.0,
        data_eng_score=95.0,
        cloud_score=85.0,
        preference_score=90.0,
        total_weighted_score=91.5,
    )
    assert fit.overall_score == 91.5


def test_ats_report_contract_and_aliases():
    c1 = ATSScoreComponent(name="Keyword Coverage", score=92.0, weight=0.25, weighted_score=23.0, explanation="Strong match")
    report = ATSReport(
        resume_id="res_001",
        job_id="job_001",
        job_title="AI Data Engineer",
        target_strategy="AI_DATA_ENGINEER",
        overall_score=94.5,
        score_interpretation="Excellent ATS Alignment",
        components={"keyword_coverage": c1},
    )
    assert report.overall_score == 94.5
    assert report.score == 94.5
    assert report.keyword_coverage is not None
    assert report.keyword_alignment is not None
    assert report.keyword_alignment.keyword_score == 92.0

    # Serialization round trip
    data = report.model_dump()
    restored = ATSReport.model_validate(data)
    assert restored.overall_score == 94.5
    assert restored.keyword_alignment.score == 92.0


def test_interview_plan_contract_and_properties():
    ans = InterviewAnswer(
        answer_id="ans_001",
        question_id="q_001",
        direct_answer="We use Apache Airflow.",
        explanation="Airflow orchestrates DAGs.",
        candidate_example="At Cognizant, built DAGs.",
        technical_details="Sensor tasks and retries.",
        result_impact="Reduced failures by 75%.",
        short_version="Short Airflow answer.",
        standard_version="Standard Airflow answer.",
        detailed_version="Detailed Airflow answer.",
    )
    assert ans.short_answer == "Short Airflow answer."
    assert ans.standard_answer == "Standard Airflow answer."
    assert ans.detailed_answer == "Detailed Airflow answer."

    day = PreparationDayPlan(day_number=1, title="Airflow Core", focus_areas=["DAGs"], practice_drills=["Drill 1"])
    assert day.theme == "Airflow Core"
    assert day.tasks == "Drill 1"

    roadmap = PreparationRoadmap(roadmap_id="road_001", target_role="AI Data Engineer", daily_schedule=[day])
    assert len(roadmap.days) == 1
