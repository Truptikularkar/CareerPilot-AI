import pytest
import uuid
from careerpilot.core.constants import ApplicationStatus, DecisionRecommendation
from careerpilot.models.application import ResumeVersionRecord
from careerpilot.db.repository import (
    ApplicationRepository,
    JobRepository,
    AnalyticsRepository,
)
from careerpilot.models.job import JobDescription


def test_application_repository_crud():
    job_id = f"job_test_{uuid.uuid4().hex[:8]}"
    app_id = f"app_test_{uuid.uuid4().hex[:8]}"

    # 1. Create a dummy job first
    jd = JobDescription(
        id=job_id,
        company_name="Acme AI",
        job_title="Senior AI Data Engineer",
        raw_text="We need Python, SQL, GCP BigQuery, Airflow, and RAG.",
    )
    JobRepository.save_job_description(jd)

    # 2. Create Application
    app = ApplicationRepository.create_application(
        app_id=app_id,
        job_id=job_id,
        company="Acme AI",
        job_title="Senior AI Data Engineer",
        job_location="Remote",
        job_url="https://acme.ai/careers/123",
        job_description_text="We need Python, SQL, GCP BigQuery, Airflow, and RAG.",
        fit_score=88.5,
        system_rec=DecisionRecommendation.APPLY,
        user_dec=DecisionRecommendation.APPLY,
        status=ApplicationStatus.ANALYZED,
        notes=["Initial parsing completed."],
    )

    assert app.application_id == app_id
    assert app.company == "Acme AI"
    assert app.fit_score == 88.5
    assert app.system_recommendation == DecisionRecommendation.APPLY
    assert app.user_decision == DecisionRecommendation.APPLY
    assert app.application_status == ApplicationStatus.ANALYZED
    assert len(app.notes) == 1

    # 3. Update Decision & Status
    updated_dec = ApplicationRepository.update_decision(app_id, DecisionRecommendation.REVIEW)
    assert updated_dec.user_decision == DecisionRecommendation.REVIEW
    assert updated_dec.system_recommendation == DecisionRecommendation.APPLY  # System rec preserved

    updated_stat = ApplicationRepository.update_status(app_id, ApplicationStatus.APPLYING, notes="Started application")
    assert updated_stat.application_status == ApplicationStatus.APPLYING
    assert len(updated_stat.notes) == 2

    # 4. Record Resume Version
    res_rec = ResumeVersionRecord(
        resume_id="res_v1_001",
        version_tag="v1.0",
        strategy_type="AI_DATA_ENGINEER",
        ats_score=94.5,
        docx_file_path="/path/to/resume.docx",
    )
    app_with_res = ApplicationRepository.record_resume_version(app_id, res_rec)
    assert len(app_with_res.resume_versions) == 1
    assert app_with_res.resume_id == "res_v1_001"
    assert app_with_res.ats_score == 94.5

    # 5. List and Filter
    apps_list = ApplicationRepository.list_applications(status=ApplicationStatus.APPLYING)
    assert any(a.application_id == app_id for a in apps_list)

    # 6. Analytics Verification
    metrics = AnalyticsRepository.get_dashboard_metrics()
    assert metrics.total_jobs_analyzed >= 1
