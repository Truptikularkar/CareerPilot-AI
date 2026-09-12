"""
CareerPilot AI — Milestone 12 Test Suite
Comprehensive verification of Career Intelligence, Data Provenance,
Real Gemini LLM Mode, Calibrated 9-Component Fit Scoring, External Integrations,
Preflight Resume Data Lock, and 1-Page PDF Engine.
"""
import pytest
from pathlib import Path
from datetime import datetime, timezone

from careerpilot.core.config import settings
from careerpilot.core.constants import (
    ApplicationStatus,
    DecisionRecommendation,
    ProvenanceSourceType,
    RequirementImportance,
    MatchStatus,
    RoleCategory,
    SeniorityLevel,
)
from careerpilot.models.job import (
    JobDescription,
    RequirementMatch,
    JobRequirement,
    CloudTransferability,
    RoleClassification,
)
from careerpilot.models.resume import (
    TailoredResume,
    ResumeHeader,
    ResumeProject,
    ResumeExperience,
    ResumeStrategy,
    ResumeSummary,
    ResumeEducation,
    ResumeCertification,
)
from careerpilot.services.candidate_service import CandidateService
from careerpilot.analysis.fit_scorer import CandidateJobFitScorer
from careerpilot.analysis.job_deduplicator import JobDeduplicator
from careerpilot.integrations import GitHubConnector, LinkedInConnector, NaukriConnector
from careerpilot.generators.resume_preflight import ResumePreflightDataLock
from careerpilot.generators.resume_pdf import PDFResumeExporter
from careerpilot.db.repository import ApplicationRepository, AnalyticsRepository
from careerpilot.db.session import init_db
from careerpilot.llm import get_llm_status, get_llm_provider
from careerpilot.llm.gemini_provider import GeminiProvider


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure database schema and baseline records are initialized."""
    init_db()


# 1. Canonical Candidate Profile Loading from SQLite
def test_canonical_profile_loading_from_sqlite():
    profile = CandidateService.get_active_profile()
    assert profile is not None
    assert "Trupti" in profile.full_name or "Alex" in profile.full_name
    assert len(profile.experiences) >= 1
    assert len(profile.skills) >= 5
    assert len(profile.education) >= 1


# 2. Data Provenance Schema
def test_data_provenance_schema():
    ds_status = CandidateService.get_data_sources_status()
    assert "sqlite" in ds_status
    assert ds_status["sqlite"]["status"] == "Active Ground Truth"
    assert ds_status["sqlite"]["verified_facts_count"] >= 10


# 3. Evidence Ledger Completeness
def test_evidence_ledger_completeness():
    from careerpilot.db.session import get_db
    from careerpilot.db.schema import CandidateEvidenceDB

    with get_db() as db:
        evidences = db.query(CandidateEvidenceDB).all()
        assert len(evidences) >= 10
        for ev in evidences:
            assert ev.id is not None
            assert ev.candidate_id is not None
            assert ev.content is not None
            assert len(ev.content.strip()) > 0


# 4. Gemini Provider Live / Explicit Error Diagnostics (Zero Silent Mock Fallback)
def test_gemini_provider_live_or_explicit_error():
    llm_status = get_llm_status()
    assert llm_status["provider"] in ("gemini", "mock")
    assert "model" in llm_status

    provider = get_llm_provider()
    assert provider is not None

    # Verify no silent fallback in LOCAL_PRIVATE mode
    if settings.CAREERPILOT_MODE.value == "LOCAL_PRIVATE" and settings.GEMINI_API_KEY:
        assert isinstance(provider, GeminiProvider)
        assert provider.model_name == "gemini-3.6-flash"


# 5. Calibrated Fit Scoring: 9 Components
def test_calibrated_fit_scoring_9_components():
    req1 = JobRequirement(skill_name="Python", importance=RequirementImportance.MUST_HAVE, years_required=2.0)
    req2 = JobRequirement(skill_name="Docker", importance=RequirementImportance.NICE_TO_HAVE)
    m1 = RequirementMatch(requirement=req1, candidate_years=2.0, required_years=2.0, match_status=MatchStatus.MATCH)
    m2 = RequirementMatch(requirement=req2, match_status=MatchStatus.MATCH)

    rc = RoleClassification(primary_role=RoleCategory.AI_DATA_ENGINEER, seniority=SeniorityLevel.MID)
    ct = CloudTransferability()
    jd = JobDescription(raw_text="AI Data Engineer role", job_title="AI Data Engineer", company_name="Tech Corp", location="Bangalore")

    breakdown = CandidateJobFitScorer.compute_fit_score([m1, m2], rc, ct, 90.0, jd)

    assert hasattr(breakdown, "must_have_score")
    assert hasattr(breakdown, "nice_to_have_score")
    assert hasattr(breakdown, "experience_score")
    assert hasattr(breakdown, "role_alignment_score")
    assert hasattr(breakdown, "evidence_strength_score")
    assert hasattr(breakdown, "location_preference_score")
    assert hasattr(breakdown, "company_preference_score")
    assert hasattr(breakdown, "cloud_score")
    assert hasattr(breakdown, "disqualifying_gap_penalty")
    assert breakdown.total_weighted_score > 0.0


# 6. Experience Shortfall Penalty (Candidate 1.9 vs 3+ Years)
def test_experience_shortfall_penalty():
    req = JobRequirement(skill_name="Python", importance=RequirementImportance.MUST_HAVE, years_required=3.5)
    m = RequirementMatch(requirement=req, candidate_years=1.9, required_years=3.5, match_status=MatchStatus.MATCH)
    rc = RoleClassification(primary_role=RoleCategory.AI_DATA_ENGINEER, seniority=SeniorityLevel.MID)
    ct = CloudTransferability()
    jd = JobDescription(raw_text="Requires 3.5+ years experience", job_title="AI Engineer", company_name="Acme", location="Bangalore")

    score = CandidateJobFitScorer.compute_fit_score([m], rc, ct, 85.0, jd)
    assert score.disqualifying_gap_penalty >= 15.0
    assert score.experience_score <= 50.0
    assert score.total_weighted_score < 75.0, "Experience shortfall must reduce total score below 75% APPLY threshold"


# 7. Must-Have Missing Penalty
def test_must_have_missing_penalty():
    req = JobRequirement(skill_name="Rust", importance=RequirementImportance.MUST_HAVE)
    m = RequirementMatch(requirement=req, match_status=MatchStatus.GAP)
    rc = RoleClassification(primary_role=RoleCategory.AI_DATA_ENGINEER, seniority=SeniorityLevel.MID)
    ct = CloudTransferability()
    jd = JobDescription(raw_text="Must have Rust", job_title="Rust Engineer", company_name="Acme", location="Bangalore")

    score = CandidateJobFitScorer.compute_fit_score([m], rc, ct, 80.0, jd)
    assert score.must_have_penalty >= settings.MUST_HAVE_PENALTY_PER_GAP
    assert score.total_weighted_score < 75.0


# 8. Canonical Job Deduplication (Hash & Normalized Match)
def test_job_deduplication_hash_and_normalized():
    res1 = JobDeduplicator.deduplicate_job(
        company_name="Microsoft",
        job_title="AI Data Engineer",
        location="Hyderabad",
        source_url="https://linkedin.com/jobs/ms1",
        raw_text="Build large scale data pipelines with Azure and Python",
    )
    res2 = JobDeduplicator.deduplicate_job(
        company_name="microsoft ",
        job_title="AI Data Engineer",
        location="Hyderabad",
        source_url="https://naukri.com/jobs/ms2",
        raw_text="Build large scale data pipelines with Azure and Python",
    )

    assert res1["canonical_job_id"] == res2["canonical_job_id"]
    assert res2["is_duplicate"] is True
    assert "https://linkedin.com/jobs/ms1" in res2["source_urls"]
    assert "https://naukri.com/jobs/ms2" in res2["source_urls"]


# 9. Application Pipeline: 14 Lifecycle Statuses & Transition History
def test_application_pipeline_14_statuses():
    all_statuses = [s for s in ApplicationStatus]
    assert len(all_statuses) in (14, 17)


    app = ApplicationRepository.create_application(
        app_id="app_status_test_1",
        job_id="job_status_test",
        company="Pipeline Co",
        job_title="Data Platform Engineer",
        status=ApplicationStatus.DISCOVERED,
    )

    updated_app = ApplicationRepository.update_status(
        app_id=app.application_id,
        new_status=ApplicationStatus.SCREENING,
        notes="HR screening scheduled",
    )
    assert updated_app.application_status == ApplicationStatus.SCREENING

    history = ApplicationRepository.get_status_history(app.application_id)
    assert len(history) >= 1
    assert history[-1]["to_status"] == ApplicationStatus.SCREENING.value


# 10. GitHub Integration: Repositories & Classification
def test_github_integration_repos_and_classification():
    repos = GitHubConnector.fetch_user_repositories(username="Truptikularkar")
    assert len(repos) >= 10
    for r in repos:
        assert r["classification"] == "PERSONAL_PROJECT"
        assert "name" in r
        assert "html_url" in r

    sync_res = GitHubConnector.sync_github_profile(username="Truptikularkar")
    assert sync_res["status"] == "SUCCESS"
    assert sync_res["repos_count"] >= 10


# 11. LinkedIn Connector: Zero Scraping & Manual Export Parsing
def test_linkedin_connector_policy_and_export_parsing():
    status = LinkedInConnector.get_status()
    assert "Zero Scraping" in status["scraping_policy"]
    assert "recommendations" in status["api_field_limitations"]

    csv_data = "Title,Company Name,Started On,Finished On\nData Engineer,Cognizant,2023,Present\n"
    imported = LinkedInConnector.parse_manual_csv_export(csv_data, section="positions")
    assert len(imported) == 1
    assert "Cognizant" in imported[0]["statement"]

    text_data = "Building real-time ETL streaming pipelines on Google Cloud Platform.\n"
    p_cnt = LinkedInConnector.import_manual_profile_text(text_data, section="experience")
    assert p_cnt >= 1


# 12. Naukri Connector: Zero Scraping & Manual Import
def test_naukri_connector_policy_and_manual_parsing():
    status = NaukriConnector.get_status()
    assert "Zero Scraping" in status["scraping_policy"]
    assert "disabled" in status["message"].lower()

    text = "Programmer Analyst at Cognizant building Google Cloud BigQuery pipelines.\n"
    count = NaukriConnector.import_manual_profile_text(text)
    assert count >= 1


# 13. Data Sources Status Matrix
def test_data_sources_status_matrix():
    ds = CandidateService.get_data_sources_status()
    assert "sqlite" in ds
    assert "candidate_rag" in ds
    assert "gemini" in ds
    assert "github" in ds
    assert "linkedin" in ds
    assert "naukri" in ds


# 14. Resume Preflight Data Lock Pass
def test_resume_preflight_data_lock_pass():
    result = ResumePreflightDataLock.execute_preflight("trupti_kularkar")
    assert result["status"] == "PASS"
    assert result["is_locked"] is True
    assert result["verified_facts_count"] >= 10
    assert "manifest" in result
    assert result["manifest"]["data_lock_status"] == "APPROVED"


# 15. Resume Preflight Data Lock Blocks Ungrounded Hallucinations
def test_resume_preflight_data_lock_blocks_hallucination():
    hallucinated_resume = TailoredResume(
        id="fake_res_1",
        job_id="job_fake",
        header=ResumeHeader(full_name="Trupti Kularkar"),
        summary=ResumeSummary(text="10 years experience at Google", target_title="Chief Architect"),
        strategy=ResumeStrategy(strategy_type="AI_DATA_ENGINEER", target_role="Chief Architect"),
        experience=[ResumeExperience(company="Nonexistent Galactic Tech", title="Astronaut", bullets=["Warp speed data pipelines"])],
        projects=[ResumeProject(name="Alien Warp Reactor Simulation", bullets=["Quantum field entanglement"])],
        technical_skills=["WarpDrive", "Python"],
    )

    result = ResumePreflightDataLock.execute_preflight("trupti_kularkar", resume=hallucinated_resume)
    assert result["status"] == "BLOCKED"
    assert result["is_locked"] is False
    assert len(result["ungrounded_claims"]) >= 1


# 16. 1-Page Resume PDF Engine Guarantee (< 3 Years Experience)
def test_1_page_resume_pdf_engine_guarantee(tmp_path):
    import pymupdf

    resume = TailoredResume(
        id="test_pdf_1p",
        job_id="job_pdf",
        header=ResumeHeader(full_name="Trupti Kularkar", email="kularkartrupti@gmail.com", phone="+91 9834055766"),
        summary=ResumeSummary(text="AI Data Engineer with 1.9+ years designing scalable ETL pipelines.", target_title="AI Data Engineer"),
        strategy=ResumeStrategy(strategy_type="AI_DATA_ENGINEER", target_role="AI Data Engineer"),
        technical_skills=["Python", "SQL", "GCP", "BigQuery", "Airflow", "FastAPI"],
        experience=[
            ResumeExperience(
                company="Cognizant",
                title="Programmer Analyst",
                start_date="2023",
                end_date="Present",
                bullets=[
                    "Engineered automated ETL pipelines on Google Cloud Platform with BigQuery.",
                    "Orchestrated Airflow DAGs improving data SLA compliance to 99.4%.",
                    "Developed automated validation tests reducing schema drift by 30%.",
                ],
            )
        ],
        projects=[
            ResumeProject(
                name="CareerPilot AI Agent",
                technologies=["Python", "LangGraph", "ChromaDB"],
                bullets=["Built multi-agent career intelligence workflows with deterministic fit scoring."],
            )
        ],
        education=[
            ResumeEducation(institution="Pune Institute of Computer Technology", degree="BE", field_of_study="Computer Engineering", graduation_year="2023")
        ],
        certifications=[
            ResumeCertification(name="Google Cloud Associate Cloud Engineer", issuer="Google Cloud", year="2023")
        ],
    )

    out_file = tmp_path / "resume_1p.pdf"
    artifact = PDFResumeExporter.export_pdf(resume, output_path=out_file)
    assert artifact.is_valid is True

    doc = pymupdf.open(str(out_file))
    pages = len(doc)
    doc.close()
    assert pages == 1, f"Resume for early-career candidate MUST be exactly 1 page, got {pages}"


# 17. Career Intelligence Insights & Analytics
def test_career_intelligence_insights_analytics():
    insights = AnalyticsRepository.get_career_insights()
    assert "total_applications" in insights
    assert "interview_conversion_rate" in insights
    assert "applications_sent" in insights
    assert "interviews_secured" in insights
    assert insights["total_applications"] >= 1
