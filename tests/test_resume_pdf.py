import pytest
import docx
from pathlib import Path
import pymupdf

from careerpilot.core.config import settings
from careerpilot.core.constants import ResumeStrategyType, TruthValidationStatus
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.generators.resume_pdf import PDFResumeExporter
from careerpilot.generators.resume_docx import DocxResumeExporter
from careerpilot.generators.resume_markdown import MarkdownResumeExporter
from careerpilot.generators.pdf_validator import PDFValidator, PDFValidationResult
from careerpilot.models.resume import TailoredResume
from careerpilot.models.artifact import ResumeArtifact, ResumeArtifactBundle
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.db.repository import ResumeRepository


@pytest.fixture(scope="module")
def tailored_resume_fixture(tmp_path_factory):
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis, override_strategy=ResumeStrategyType.AI_DATA_ENGINEER)
    
    out_dir = tmp_path_factory.mktemp("pdf_test")
    pdf_path = out_dir / "test_resume.pdf"
    docx_path = out_dir / "test_resume.docx"

    pdf_artifact = PDFResumeExporter.export_pdf(resume, pdf_path)
    docx_artifact = DocxResumeExporter.export_docx(resume, docx_path)

    return resume, pdf_path, docx_path, pdf_artifact, docx_artifact


def test_resume_generation_contract():
    """Verify TailoredResume model contract (contains content, not file I/O)."""
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis, override_strategy=ResumeStrategyType.AI_DATA_ENGINEER)

    assert isinstance(resume, TailoredResume)
    assert resume.header.full_name == "Trupti Kularkar"
    assert len(resume.experiences) > 0
    assert len(resume.skills_categories) > 0
    assert len(resume.projects) > 0
    assert resume.summary is not None
    assert resume.truth_report is not None


def test_pdf_generation_contract(tailored_resume_fixture):
    """Verify PDF exporter contract: returns ResumeArtifact with valid PDF bytes."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture

    assert isinstance(pdf_art, ResumeArtifact)
    assert pdf_art.artifact_type == "pdf"
    assert pdf_art.content_type == "application/pdf"
    assert pdf_art.is_valid is True
    assert pdf_art.file_name.endswith(".pdf")
    assert len(pdf_art.get_bytes()) > 500


def test_docx_generation_contract(tailored_resume_fixture):
    """Verify DOCX exporter contract: returns ResumeArtifact with valid docx bytes."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture

    assert isinstance(docx_art, ResumeArtifact)
    assert docx_art.artifact_type == "docx"
    assert "wordprocessingml" in docx_art.content_type
    assert docx_art.file_name.endswith(".docx")
    assert len(docx_art.get_bytes()) > 500


def test_pdf_validation(tailored_resume_fixture):
    """Verify PDFValidator inspects PDF structure, single column, and extractable text."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture
    val_result = PDFValidator.validate_pdf(pdf_path, candidate_name=resume.header.full_name)

    assert isinstance(val_result, PDFValidationResult)
    assert val_result.status in ("PASS", "WARNING")
    assert val_result.page_count >= 1
    assert val_result.total_words >= 50
    assert val_result.is_searchable is True
    assert val_result.is_single_column is True
    assert val_result.candidate_name_detected is True


def test_docx_validation(tailored_resume_fixture):
    """Verify DOCX file opens and contains candidate name, summary, and experience."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture
    doc = docx.Document(str(docx_path))
    doc_text = " ".join(p.text for p in doc.paragraphs)

    assert resume.header.full_name in doc_text
    assert "PROFESSIONAL SUMMARY" in doc_text or "Summary" in doc_text
    assert "EXPERIENCE" in doc_text or "Experience" in doc_text


def test_pdf_download_artifact(tailored_resume_fixture):
    """Verify PDF artifact supplies raw binary stream for Streamlit download button."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture
    raw_bytes = pdf_art.get_bytes()

    assert isinstance(raw_bytes, bytes)
    assert len(raw_bytes) > 500
    assert raw_bytes.startswith(b"%PDF")


def test_docx_download_artifact(tailored_resume_fixture):
    """Verify DOCX artifact supplies raw binary stream for Streamlit download button."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture
    raw_bytes = docx_art.get_bytes()

    assert isinstance(raw_bytes, bytes)
    assert len(raw_bytes) > 500
    assert raw_bytes.startswith(b"PK")  # ZIP / OOXML magic header


def test_resume_version_consistency():
    """Verify that multiple resume versions maintain distinct tags and correct artifacts."""
    job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis, app = CareerPilotService.analyze_job(job_file, company_name="CognitiveScale Labs", job_title="AI Data Engineer")

    # Generate Version 1
    r1, ats1, app1 = CareerPilotService.generate_resume_for_application(app.application_id, strategy=ResumeStrategyType.AI_DATA_ENGINEER)
    # Generate Version 2
    r2, ats2, app2 = CareerPilotService.generate_resume_for_application(app.application_id, strategy=ResumeStrategyType.DATA_ENGINEER)

    versions = ResumeRepository.list_versions_for_job(app.job_id)
    assert len(versions) >= 2
    assert versions[0].version_tag != versions[1].version_tag
    assert versions[0].docx_file_path != versions[1].docx_file_path


def test_tailored_resume_does_not_need_pdf_path():
    """
    Regression Test:
    Ensures TailoredResume domain model is purely for content and that the export
    pipeline functions properly without needing or relying on `resume.pdf_path`.
    """
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis)

    # Pure domain model - generate artifacts via dedicated exporters
    pdf_art = PDFResumeExporter.export_pdf(resume)
    assert isinstance(pdf_art, ResumeArtifact)
    assert pdf_art.is_valid is True
    assert Path(pdf_art.file_path).exists()

    docx_art = DocxResumeExporter.export_docx(resume)
    assert isinstance(docx_art, ResumeArtifact)
    assert Path(docx_art.file_path).exists()


def test_service_get_or_generate_resume_artifacts():
    """Verify that CareerPilotService generates complete ResumeArtifactBundle."""
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis)

    bundle = CareerPilotService.get_or_generate_resume_artifacts(resume, company="TestCorp")
    assert isinstance(bundle, ResumeArtifactBundle)
    assert bundle.pdf is not None
    assert bundle.docx is not None
    assert bundle.markdown is not None
    assert bundle.pdf.is_valid is True
    assert "TestCorp" in bundle.pdf.file_name


def test_pdf_searchability(tailored_resume_fixture):
    """Verify that core verified skills are fully searchable in the PDF."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture
    doc = pymupdf.open(str(pdf_path))
    text = "\n".join(page.get_text("text") for page in doc)
    doc.close()

    for term in ["Python", "SQL", "BigQuery", "Airflow", "GCP"]:
        assert term.lower() in text.lower(), f"Expected term '{term}' to be searchable in PDF."


def test_docx_pdf_content_consistency(tailored_resume_fixture):
    """Verify that meaningful resume content is consistent between DOCX and PDF."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture

    # Extract text from DOCX
    doc = docx.Document(str(docx_path))
    docx_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    # Extract text from PDF
    pdf_doc = pymupdf.open(str(pdf_path))
    pdf_text = "\n".join(page.get_text("text") for page in pdf_doc)
    pdf_doc.close()

    # Verify candidate name in both
    assert resume.header.full_name in docx_text
    assert resume.header.full_name in pdf_text

    # Verify first experience bullet appears in both
    if resume.experiences and resume.experiences[0].bullets:
        sample_bullet = resume.experiences[0].bullets[0]
        sample_snippet = sample_bullet[:30]
        assert sample_snippet in docx_text
        assert sample_snippet in pdf_text


def test_safe_filename():
    """Verify that unsafe filesystem characters are sanitized."""
    raw_name = 'Trupti/Kularkar: "AI*Engineer"?'
    safe = PDFResumeExporter.get_safe_filename(raw_name, "Data/ML Lead", "Acme | Corp")
    assert "/" not in safe
    assert "\\" not in safe
    assert ":" not in safe
    assert "*" not in safe
    assert "?" not in safe
    assert '"' not in safe
    assert "<" not in safe
    assert ">" not in safe
    assert "|" not in safe
    assert safe.endswith(".pdf")


def test_metric_integrity(tailored_resume_fixture):
    """Verify that verified metrics (e.g. 25% or 35%) are not inflated or altered."""
    resume, pdf_path, docx_path, pdf_art, docx_art = tailored_resume_fixture
    pdf_doc = pymupdf.open(str(pdf_path))
    pdf_text = "\n".join(page.get_text("text") for page in pdf_doc)
    pdf_doc.close()

    assert "25%" in pdf_text or "35%" in pdf_text
    assert "99.9%" not in pdf_text


def test_empty_resume_handling(tmp_path):
    """Verify that PDFValidator handles missing and empty files gracefully."""
    res1 = PDFValidator.validate_pdf(tmp_path / "non_existent.pdf")
    assert res1.status == "FAIL"
    assert res1.candidate_name_detected is False

    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    res2 = PDFValidator.validate_pdf(empty_file)
    assert res2.status == "FAIL"
    assert res2.file_size_bytes == 0


def test_truth_guard_blocks_unsupported_claim(tmp_path):
    """Verify that when Truth Guard blocks a claim, export_artifacts_node does NOT create a verified PDF."""
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis, override_strategy=ResumeStrategyType.AI_DATA_ENGINEER)
    
    import uuid
    resume.id = f"resume_blocked_{uuid.uuid4().hex[:8]}"
    resume.experiences[0].bullets.append("5+ years of professional experience as AWS data engineer in production.")
    
    from careerpilot.truth_guard.validator import TruthValidator
    truth_report = TruthValidator.validate_tailored_resume(resume)
    assert truth_report.status == TruthValidationStatus.BLOCK

    from careerpilot.graphs.resume_graph import export_artifacts_node
    state = {
        "draft_resume": resume,
        "job_analysis": analysis,
        "strategy": resume.strategy,
        "truth_report": truth_report,
        "ats_precheck": None,
    }
    result = export_artifacts_node(state)
    out_dir = Path(result["output_dir"])
    
    assert not (out_dir / "resume.pdf").exists()
    assert not (out_dir / "resume.docx").exists()


def test_aws_negative_test():
    """Verify that analyzing an AWS-heavy JD does not falsely claim production AWS experience on resume."""
    eval_job_file = settings.EVALUATION_JOBS_DIR / "04_gcp_cloud_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis)
    
    exp_text = " ".join(" ".join(e.bullets) for e in resume.experiences)
    assert "production AWS EKS" not in exp_text
    assert "Redshift production lead" not in exp_text


def test_all_strategies_pdf_generation(tmp_path):
    """Verify that PDF generation succeeds for all 4 supported strategies."""
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)

    for strat in [
        ResumeStrategyType.AI_DATA_ENGINEER,
        ResumeStrategyType.DATA_ENGINEER,
        ResumeStrategyType.GENAI_ENGINEER,
        ResumeStrategyType.GCP_DATA_ENGINEER,
    ]:
        resume = generate_tailored_resume(analysis, override_strategy=strat)
        pdf_path = tmp_path / f"resume_{strat.value}.pdf"
        art = PDFResumeExporter.export_pdf(resume, pdf_path)
        assert isinstance(art, ResumeArtifact)
        assert Path(pdf_path).exists()
        assert Path(pdf_path).stat().st_size > 500
        val = PDFValidator.validate_pdf(pdf_path, candidate_name=resume.header.full_name)
        assert val.status in ("PASS", "WARNING")
