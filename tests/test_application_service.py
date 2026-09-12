import pytest
from pathlib import Path
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import DecisionRecommendation, ApplicationStatus, ResumeStrategyType


def test_careerpilot_service_analyze_and_manage_application():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")

    # 1. Analyze Job
    analysis, app = CareerPilotService.analyze_job(
        input_source=eval_file,
        company_name="Google Vertex Team",
        job_title="Lead AI Data Engineer",
        job_location="Bangalore / Hybrid",
    )

    assert analysis is not None
    assert app is not None
    assert app.company == "Google Vertex Team"
    assert app.job_title == "Lead AI Data Engineer"
    assert app.fit_score > 70.0
    assert app.system_recommendation in (DecisionRecommendation.APPLY, DecisionRecommendation.REVIEW)
    assert app.application_status == ApplicationStatus.ANALYZED

    # 2. Update Decision (User Override)
    updated_app = CareerPilotService.update_application_decision(app.application_id, DecisionRecommendation.APPLY)
    assert updated_app.user_decision == DecisionRecommendation.APPLY

    # 3. Add Note
    app_with_note = CareerPilotService.add_application_note(app.application_id, "Connected with hiring manager on LinkedIn.")
    assert len(app_with_note.notes) >= 1

    # 4. Generate Resume
    resume, ats_report, app_res = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.AI_DATA_ENGINEER,
    )
    assert resume is not None
    assert ats_report.overall_score >= 80.0
    assert len(app_res.resume_versions) >= 1
    assert app_res.resume_id == resume.id

    # 5. Evaluate ATS
    ats_rep2 = CareerPilotService.evaluate_ats_for_application(app.application_id)
    assert ats_rep2.overall_score == ats_report.overall_score

    # 6. Prepare Interview
    prep_state = CareerPilotService.prepare_interview_for_application(app.application_id, roadmap_days=7)
    assert len(prep_state.get("questions", [])) >= 10
    app_prep = CareerPilotService.get_application(app.application_id)
    assert app_prep.interview_status == "Prepared"

    # 7. Dashboard Metrics
    metrics = CareerPilotService.get_dashboard_metrics()
    assert metrics.total_jobs_analyzed >= 1
