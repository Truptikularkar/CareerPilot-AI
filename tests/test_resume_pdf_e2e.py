import pytest
from pathlib import Path

from careerpilot.core.config import settings
from careerpilot.core.constants import ResumeStrategyType, DecisionRecommendation, TruthValidationStatus
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.generators.pdf_validator import PDFValidator
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import ATSReport
from careerpilot.models.artifact import ResumeArtifact, ResumeArtifactBundle


def test_resume_pdf_end_to_end_pipeline():
    """
    End-to-end verification of the full resume workflow:
    Job Analysis -> Apply -> Tailored Resume -> Truth Guard -> ATS -> DOCX + PDF -> Validation -> Artifact Bundle.
    """
    # 1. Job Analysis
    job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis, app = CareerPilotService.analyze_job(
        input_source=job_file,
        company_name="CognitiveScale Labs",
        job_title="AI Data Engineer",
    )
    assert analysis.job_id is not None
    assert app.application_id is not None

    # 2. Resume Tailoring (DOCX + PDF)
    resume, ats_report, updated_app = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.AI_DATA_ENGINEER,
    )
    assert isinstance(resume, TailoredResume)
    assert isinstance(ats_report, ATSReport)
    assert resume.truth_report.status == TruthValidationStatus.PASS
    assert ats_report.overall_score >= 85.0

    # 3. Artifact Bundle Retrieval from Service
    artifacts = CareerPilotService.get_or_generate_resume_artifacts(resume, company=app.company)
    assert isinstance(artifacts, ResumeArtifactBundle)
    assert artifacts.pdf is not None
    assert artifacts.docx is not None
    assert Path(artifacts.pdf.file_path).exists()
    assert Path(artifacts.docx.file_path).exists()
    assert len(artifacts.pdf.get_bytes()) > 500
    assert len(artifacts.docx.get_bytes()) > 500

    # 4. Deterministic PDF Validation
    pdf_val = PDFValidator.validate_pdf(artifacts.pdf.file_path, candidate_name=resume.header.full_name)
    assert pdf_val.status in ("PASS", "WARNING")
    assert pdf_val.page_count >= 1
    assert pdf_val.is_searchable is True
    assert pdf_val.is_single_column is True
    assert pdf_val.candidate_name_detected is True

    # 5. Application Record Check
    latest_app = CareerPilotService.get_application(app.application_id)
    assert latest_app is not None
    assert len(latest_app.resume_versions) > 0
    latest_ver = latest_app.resume_versions[-1]
    assert latest_ver.pdf_file_path == artifacts.pdf.file_path
    assert latest_ver.docx_file_path == artifacts.docx.file_path
