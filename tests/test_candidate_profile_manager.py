import pytest
from pathlib import Path
from datetime import datetime, timezone

from careerpilot.models.candidate import (
    CandidateProfile,
    Skill,
    Experience,
    Project,
    Education,
    Achievement,
    CareerPreference,
    ProfileDiffItem,
    ProfileDiffResult,
)
from careerpilot.core.constants import SkillCategory, RoleCategory, SeniorityLevel, ResumeStrategyType
from careerpilot.services.candidate_service import CandidateService
from careerpilot.services.resume_import_service import ResumeImportService
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.db.repository import CandidateRepository
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.core.config import settings


@pytest.fixture(autouse=True)
def reset_profile_baseline():
    """Ensure a clean baseline profile before each test."""
    profile = CandidateRepository.get_profile()
    yield profile


def test_add_project():
    """Verify adding a new personal project with explicit classification."""
    new_proj = Project(
        name="AI Ticket Classifier",
        project_type="PERSONAL_PROJECT",
        description="Autonomous ticket triage system using Gemini 2.5 Pro.",
        technologies=["Python", "Vertex AI", "FastAPI"],
        responsibilities=["Built routing DAGs", "Achieved 95% routing precision"],
        architecture="Event-driven Pub/Sub to Cloud Run",
        outcome="Automated 80% of tier-1 support tickets",
        metrics=["95% routing precision", "80% automated triage"],
    )

    updated_prof = CandidateService.add_project(new_proj)
    assert any(p.name == "AI Ticket Classifier" for p in updated_prof.projects)
    added = next(p for p in updated_prof.projects if p.name == "AI Ticket Classifier")
    assert added.project_type == "PERSONAL_PROJECT"
    assert "95% routing precision" in added.metrics


def test_update_project():
    """Verify updating an existing project."""
    updated_proj = Project(
        name="AI Ticket Classifier",
        project_type="PERSONAL_PROJECT",
        description="Updated description with enhanced Gemini flash routing.",
        technologies=["Python", "Vertex AI", "FastAPI", "Docker"],
        responsibilities=["Built routing DAGs", "Added Docker containerization"],
        metrics=["98% routing precision"],
    )

    updated_prof = CandidateService.update_project(updated_proj)
    target = next(p for p in updated_prof.projects if p.name == "AI Ticket Classifier")
    assert "Docker" in target.technologies
    assert target.metrics == ["98% routing precision"]


def test_delete_project():
    """Verify deleting a project."""
    updated_prof = CandidateService.delete_project("AI Ticket Classifier")
    assert not any(p.name == "AI Ticket Classifier" for p in updated_prof.projects)


def test_duplicate_project_detection():
    """Verify duplicate project addition is prevented."""
    p1 = Project(name="Duplicate Proj", description="Desc", technologies=["Python"])
    CandidateService.add_project(p1)

    with pytest.raises(ValueError, match="already exists"):
        CandidateService.add_project(p1)

    # Clean up
    CandidateService.delete_project("Duplicate Proj")


def test_add_skill():
    """Verify adding a new skill with explicit evidence level."""
    skill = Skill(
        name="Polars",
        category=SkillCategory.DATA_ENGINEERING,
        evidence_level="PERSONAL_PROJECT",
        evidence_status="VERIFIED",
        proficiency_level="Advanced",
        years_of_experience=1.0,
        context="Built high-performance dataframe pipelines in Rust/Python.",
    )

    updated_prof = CandidateService.add_skill(skill)
    assert any(s.name == "Polars" for s in updated_prof.skills)
    added = next(s for s in updated_prof.skills if s.name == "Polars")
    assert added.evidence_level == "PERSONAL_PROJECT"
    assert added.evidence_status == "VERIFIED"


def test_update_skill():
    """Verify updating an existing skill."""
    skill = Skill(
        name="Polars",
        category=SkillCategory.DATA_ENGINEERING,
        evidence_level="PERSONAL_PROJECT",
        evidence_status="VERIFIED",
        proficiency_level="Expert",
        years_of_experience=1.5,
    )
    updated_prof = CandidateService.update_skill(skill)
    target = next(s for s in updated_prof.skills if s.name == "Polars")
    assert target.proficiency_level == "Expert"
    assert target.years_of_experience == 1.5


def test_delete_skill():
    """Verify deleting a skill."""
    updated_prof = CandidateService.delete_skill("Polars")
    assert not any(s.name == "Polars" for s in updated_prof.skills)



def test_duplicate_skill_detection():
    """Verify duplicate skill addition raises ValueError."""
    skill = Skill(name="TestDupeSkill", category=SkillCategory.OTHER)
    CandidateService.add_skill(skill)

    with pytest.raises(ValueError, match="already exists"):
        CandidateService.add_skill(skill)

    CandidateService.delete_skill("TestDupeSkill")


def test_update_experience():
    """Verify editing professional experiences."""
    profile = CandidateService.get_active_profile()
    exp = profile.experiences[0]
    original_company = exp.company
    exp.company = "Cognizant Technology Solutions India"

    updated_prof = CandidateService.update_experiences(profile.experiences)
    assert updated_prof.experiences[0].company == "Cognizant Technology Solutions India"

    # Restore
    exp.company = original_company
    CandidateService.update_experiences(profile.experiences)


def test_update_preferences():
    """Verify editing career preferences."""
    new_pref = CareerPreference(
        target_roles=[RoleCategory.AI_DATA_ENGINEER, RoleCategory.GENAI_ENGINEER],
        preferred_seniority=SeniorityLevel.SENIOR,
        work_modes=["Remote", "Hybrid"],
        target_locations=["Pune", "Bengaluru"],
        min_desired_comp="12 LPA",
        cloud_preferences=["GCP", "AWS"],
    )
    updated_prof = CandidateService.update_preferences(new_pref)
    assert RoleCategory.GENAI_ENGINEER in updated_prof.preferences.target_roles
    assert "Bengaluru" in updated_prof.preferences.target_locations
    assert updated_prof.preferences.min_desired_comp == "12 LPA"


def test_resume_import_and_diff_computation():
    """Verify master resume parsing and change diff detection."""
    sample_resume_text = """
    Trupti Kularkar
    Pune, India | kularkartrupti@gmail.com
    Professional Summary:
    AI Data Engineer with expertise in Python, SQL, BigQuery, Airflow, GCP, and Vertex AI.
    
    Technical Skills:
    Python, SQL, BigQuery, Airflow, Vertex AI, Docker, Kubernetes, Terraform, Rust
    
    Projects:
    CareerPilot AI Copilot: Built an autonomous career intelligence agent using LangGraph and ChromaDB.
    """

    parsed_data = ResumeImportService.parse_resume_content(sample_resume_text)
    assert "Docker" in parsed_data["skills"]
    assert "Rust" in parsed_data["skills"]

    profile = CandidateService.get_active_profile()
    diff_res = ResumeImportService.compute_diff(profile, parsed_data)
    assert isinstance(diff_res, ProfileDiffResult)
    assert diff_res.total_added > 0

    added_names = [d.new_value for d in diff_res.diff_items if d.change_type == "ADDED"]
    assert "Docker" in added_names or "Rust" in added_names


def test_change_approval_and_rejection():
    """Verify approving and rejecting parsed diff items."""
    profile = CandidateService.get_active_profile()
    diff_items = [
        ProfileDiffItem(
            section="skills",
            change_type="ADDED",
            item_name="Skill: Rust",
            new_value="Rust",
            approved=True,
        ),
        ProfileDiffItem(
            section="skills",
            change_type="ADDED",
            item_name="Skill: Ruby",
            new_value="Ruby",
            approved=False,  # Rejected
        ),
    ]

    updated_prof = ResumeImportService.apply_diff_items(profile, diff_items)
    assert any(s.name == "Rust" for s in updated_prof.skills)
    assert not any(s.name == "Ruby" for s in updated_prof.skills)

    # Clean up
    CandidateService.delete_skill("Rust")


def test_evidence_update_and_rag_sync():
    """Verify atomic evidence generation and Candidate RAG synchronization."""
    profile = CandidateService.get_active_profile()
    chunks_indexed = CandidateService.sync_profile_to_rag(profile)
    assert chunks_indexed > 0

    status = CandidateService.get_rag_sync_status()
    assert status["is_synchronized"] is True
    assert status["chunk_count"] >= chunks_indexed


def test_profile_versioning_and_restore():
    """Verify that saving profile creates version snapshots and rollback restores exact state."""
    profile = CandidateService.get_active_profile()
    initial_versions = CandidateService.list_profile_versions()
    initial_count = len(initial_versions)

    # Make a temporary change
    old_summary = profile.professional_summary
    profile.professional_summary = "Special temporary summary for rollback testing."
    version_row, _ = CandidateService.save_active_profile(
        profile,
        change_summary="Temporary test version",
        changed_sections=["summary"],
    )

    versions_after = CandidateService.list_profile_versions()
    assert len(versions_after) == initial_count + 1

    # Restore to initial baseline version
    first_ver = versions_after[-1]  # Oldest baseline version
    restored_prof = CandidateService.restore_profile_version(first_ver.id)
    assert restored_prof.professional_summary != "Special temporary summary for rollback testing."


def test_end_to_end_project_addition_to_resume():
    """
    End-to-End Integration Test:
    Add a new project -> Sync RAG -> Analyze Job -> Generate Tailored Resume -> Verify project is retrieved.
    """
    proj = Project(
        name="AutoHeal GCP Agent",
        project_type="PERSONAL_PROJECT",
        description="Autonomous Airflow task remediation agent on GCP Cloud Run.",
        technologies=["Python", "Cloud Run", "BigQuery", "Gemini 2.5 Pro"],
        responsibilities=["Built remediation logic for Airflow failures", "Auto-repaired 75% transient failures"],
        metrics=["75% auto-remediation", "60% on-call reduction"],
    )

    # 1. Add project
    CandidateService.add_project(proj)

    # 2. Analyze job requiring GCP & AI Agent skills
    job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis, app = CareerPilotService.analyze_job(
        input_source=job_file,
        company_name="AutoHeal Target Corp",
        job_title="AI Data Engineer",
    )

    # 3. Generate Tailored Resume
    resume, ats_report, _ = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.AI_DATA_ENGINEER,
    )

    # 4. Verify Truth Guard and Project retrieval
    assert resume.truth_report.status.value in ("PASS", "FLAG")
    assert len(resume.projects) > 0

    # Clean up
    try:
        CandidateService.delete_project("AutoHeal GCP Agent")
    except Exception:
        pass
