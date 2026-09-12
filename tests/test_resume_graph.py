import pytest
from pathlib import Path
from careerpilot.core.config import settings
from careerpilot.core.constants import TruthValidationStatus
from careerpilot.graphs.resume_graph import generate_tailored_resume


def test_resume_generation_5_representative_jobs():
    test_jds = [
        "01_ai_data_engineer.txt",
        "02_data_engineer_gcp.txt",
        "03_genai_rag_engineer.txt",
        "04_gcp_cloud_data_engineer.txt",
        "05_aws_data_engineer_transferable.txt",
    ]

    generated_ids = set()

    for jd_name in test_jds:
        eval_path = settings.EVALUATION_JOBS_DIR / jd_name
        resume = generate_tailored_resume(eval_path)

        assert resume is not None
        assert resume.id not in generated_ids
        generated_ids.add(resume.id)

        # Verify truth validation passed
        assert resume.truth_report.status in (TruthValidationStatus.PASS, TruthValidationStatus.FLAG)
        assert len(resume.truth_report.blocked_claims) == 0

        # Verify artifacts exist in unique resume folder
        resume_dir = settings.OUTPUT_RESUMES_DIR / resume.id
        assert resume_dir.exists()
        assert (resume_dir / "resume.md").exists()
        assert (resume_dir / "resume.docx").exists()
        assert (resume_dir / "resume_audit.json").exists()
        assert (resume_dir / "truth_report.md").exists()
        assert (resume_dir / "strategy.json").exists()
