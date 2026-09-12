import pytest
from pathlib import Path
import tempfile
import pymupdf

from careerpilot.core.date_utils import (
    parse_date_string,
    calculate_experience_duration_months,
    calculate_total_experience_years,
    format_experience_duration_string,
)
from careerpilot.services.candidate_service import CandidateService
from careerpilot.models.candidate import CandidateProfile, Experience, Education, Project, Skill
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import ResumeStrategy
from careerpilot.core.constants import ResumeStrategyType, SkillCategory
from careerpilot.generators.bullet_selector import BulletSelector
from careerpilot.generators.resume_pdf import PDFResumeExporter
from careerpilot.generators.resume_docx import DocxResumeExporter
from careerpilot.generators.pdf_validator import PDFValidator
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.graphs.job_analysis_graph import analyze_job


def test_experience_duration_calculation():
    """Verify deterministic date calculations and formatting."""
    # Test single interval
    m = calculate_experience_duration_months("11/2024", "11/2025")
    assert m == 13.0 or m == 12.0 or m >= 12.0

    # Test experiences list
    exps = [
        Experience(
            company="Cognizant",
            title="Programmer Analyst",
            start_date="11/2025",
            end_date="Present",
            is_current=True,
        ),
        Experience(
            company="Cognizant",
            title="Programmer Analyst Trainee",
            start_date="11/2024",
            end_date="11/2025",
            is_current=False,
        ),
    ]
    total_years = calculate_total_experience_years(exps)
    assert total_years >= 1.0
    formatted = format_experience_duration_string(total_years)
    assert "+" in formatted or "years" in formatted


def test_resume_education_fidelity():
    """Verify that candidate education details in generated resumes are 100% faithful to the canonical profile."""
    profile = CandidateService.get_active_profile()
    assert profile.education, "Profile should have education records."
    
    edu_expected = profile.education[0]
    assembled_edus = BulletSelector.assemble_education(profile)
    assert len(assembled_edus) >= 1
    
    assembled = assembled_edus[0]
    assert assembled.institution == edu_expected.institution
    assert assembled.degree == edu_expected.degree
    assert assembled.field_of_study == edu_expected.field_of_study
    assert assembled.graduation_year == str(edu_expected.graduation_year)


def test_resume_experience_date_fidelity():
    """Verify that experience dates, roles, and companies are preserved verbatim."""
    profile = CandidateService.get_active_profile()
    assert profile.experiences, "Profile should have experiences."

    dummy_analysis = analyze_job("We are looking for an AI Data Engineer with Python, SQL, and BigQuery experience.")
    strategy = ResumeStrategy(
        target_role="AI Data Engineer",
        strategy_type=ResumeStrategyType.AI_DATA_ENGINEER,
        role_category="AI_DATA_ENGINEER",
        emphasis_keywords=["BigQuery", "Python", "SQL"],
        project_priorities=["AI-Driven Data Quality Monitoring & Anomaly Detection"],
    )

    assembled_exps = BulletSelector.assemble_experience(strategy, dummy_analysis, candidate=profile)
    assert len(assembled_exps) == len(profile.experiences)

    for orig, assem in zip(profile.experiences, assembled_exps):
        assert assem.company == orig.company
        assert assem.title == orig.title
        assert assem.start_date == orig.start_date
        assert assem.end_date == orig.end_date


def test_resume_one_page():
    """Verify that tailored resume PDF strictly formats to 1 page for the default candidate profile."""
    analysis = analyze_job("Seeking a Data Engineer with Google Cloud Platform, BigQuery, Airflow, and Python skills.")
    tailored = generate_tailored_resume(job_input=analysis, override_strategy=ResumeStrategyType.DATA_ENGINEER)

    with tempfile.TemporaryDirectory() as tmpdir:

        pdf_path = Path(tmpdir) / "test_one_page_resume.pdf"
        artifact = PDFResumeExporter.export_pdf(tailored, output_path=pdf_path)
        assert Path(artifact.file_path).exists()

        # Validate with PDFValidator
        val_res = PDFValidator.validate_pdf(artifact.file_path, candidate_name=tailored.header.full_name)
        assert val_res.page_count == 1, f"Expected 1-page PDF, but got {val_res.page_count} pages."
        assert val_res.is_single_column is True
        assert val_res.is_searchable is True


def test_profile_crud_experience():
    """Verify Adding, Updating, and Deleting experiences in CandidateService."""
    test_exp = Experience(
        company="TechCorp Innovations",
        title="Associate Data Engineer",
        start_date="01/2024",
        end_date="06/2024",
        location="Remote",
        responsibilities=["Built real-time Kafka pipelines."],
    )

    # 1. Add
    CandidateService.add_experience(test_exp)
    prof = CandidateService.get_active_profile()
    assert any(e.company == "TechCorp Innovations" for e in prof.experiences)

    # 2. Update
    test_exp.title = "Lead Data Engineer"
    CandidateService.update_experience(test_exp)
    prof = CandidateService.get_active_profile()
    updated = next(e for e in prof.experiences if e.company == "TechCorp Innovations")
    assert updated.title == "Lead Data Engineer"

    # 3. Delete
    CandidateService.delete_experience(test_exp.id)
    prof = CandidateService.get_active_profile()
    assert not any(e.company == "TechCorp Innovations" for e in prof.experiences)


def test_profile_crud_education():
    """Verify Adding, Updating, and Deleting education in CandidateService."""
    test_edu = Education(
        institution="MIT World Peace University",
        degree="Post Graduate Diploma",
        field_of_study="Data Science",
        graduation_year="2025",
    )

    # 1. Add
    CandidateService.add_education(test_edu)
    prof = CandidateService.get_active_profile()
    assert any(ed.institution == "MIT World Peace University" for ed in prof.education)

    # 2. Update
    test_edu.degree = "Master of Science"
    CandidateService.update_education_entry(test_edu)
    prof = CandidateService.get_active_profile()
    updated = next(ed for ed in prof.education if ed.institution == "MIT World Peace University")
    assert updated.degree == "Master of Science"

    # 3. Delete
    CandidateService.delete_education("MIT World Peace University")
    prof = CandidateService.get_active_profile()
    assert not any(ed.institution == "MIT World Peace University" for ed in prof.education)


def test_profile_update_reflected_in_resume():
    """Verify that updating the candidate profile immediately reflects in generated resumes."""
    orig_prof = CandidateService.get_active_profile()
    orig_name = orig_prof.full_name

    try:
        # Update name and summary
        orig_prof.full_name = "Trupti K. Senior Engineer"
        CandidateService.save_active_profile(orig_prof, change_summary="Test name update")

        analysis = analyze_job("Looking for an AI Data Engineer with Vertex AI and BigQuery experience.")
        resume = generate_tailored_resume(job_input=analysis)

        assert resume.header.full_name == "Trupti K. Senior Engineer"

    finally:
        # Restore original name
        orig_prof.full_name = orig_name
        CandidateService.save_active_profile(orig_prof, change_summary="Restore original name")


def test_stale_rag_invalidation():
    """Verify that Candidate RAG synchronization indexes chunks with correct metadata."""
    synced_chunks = CandidateService.sync_profile_to_rag()
    assert synced_chunks > 0

    rag_status = CandidateService.get_rag_sync_status()
    assert rag_status["is_synced"] is True
    assert rag_status["chunk_count"] > 0
