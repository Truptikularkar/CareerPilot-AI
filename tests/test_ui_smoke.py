import pytest
from pathlib import Path
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import (
    ApplicationStatus,
    DecisionRecommendation,
    ResumeStrategyType,
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
)
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.application import Application, DashboardMetrics
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import ATSReport
from careerpilot.models.interview import InterviewPlan
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation, FinalInterviewReport
from careerpilot.core.config import settings


@pytest.fixture(scope="module")
def sample_job_analysis():
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis, app = CareerPilotService.analyze_job(
        input_source=eval_job_file,
        company_name="Acme AI Corp",
        job_title="AI Data Engineer",
    )
    return analysis, app


def test_dashboard_load():
    """Verify that dashboard metrics and application listings load without errors."""
    metrics = CareerPilotService.get_dashboard_metrics()
    assert isinstance(metrics, DashboardMetrics)
    assert metrics.total_jobs_analyzed >= 0

    apps = CareerPilotService.list_applications()
    assert isinstance(apps, list)


def test_job_analysis_action(sample_job_analysis):
    """Verify Job Analysis action output structure, fit score, and seniority."""
    analysis, app = sample_job_analysis
    assert isinstance(analysis, JobAnalysisResult)
    assert isinstance(app, Application)
    assert analysis.fit_score.overall_score >= 0.0
    assert analysis.role_classification.primary_role is not None
    assert analysis.seniority_detection.detected_seniority is not None
    # Verify backward-compatibility property
    assert analysis.seniority_detection.estimated_level == analysis.seniority_detection.detected_seniority
    assert analysis.cloud_transferability.primary_target_cloud is not None


def test_application_creation_and_update(sample_job_analysis):
    """Verify application state updates, decision overrides, and note additions."""
    analysis, app = sample_job_analysis
    
    # 1. Update Decision
    updated_app = CareerPilotService.update_application_decision(
        app_id=app.application_id,
        user_decision=DecisionRecommendation.APPLY,
    )
    assert updated_app.user_decision == DecisionRecommendation.APPLY

    # 2. Add Note
    noted_app = CareerPilotService.add_application_note(
        app_id=app.application_id,
        note_text="Recruiter interview scheduled.",
    )
    assert any("Recruiter interview scheduled." in n for n in noted_app.notes)

    # 3. Update Status
    status_app = CareerPilotService.update_application_status(
        app_id=app.application_id,
        new_status=ApplicationStatus.INTERVIEW,
        notes="Moved to first round technical screening",
    )
    assert status_app.application_status == ApplicationStatus.INTERVIEW


def test_resume_generation_action(sample_job_analysis):
    """Verify resume tailoring action, Truth Guard validation, and artifact export."""
    analysis, app = sample_job_analysis
    resume, ats_report, updated_app = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.AI_DATA_ENGINEER,
    )
    assert isinstance(resume, TailoredResume)
    assert isinstance(ats_report, ATSReport)
    assert resume.truth_report is not None
    assert resume.truth_report.status.value in ("PASS", "FLAG", "BLOCK")
    assert ats_report.overall_score > 0.0
    assert ats_report.keyword_alignment is not None
    assert ats_report.keyword_alignment.score > 0.0


def test_ats_analysis_action(sample_job_analysis):
    """Verify ATS report evaluation and component access."""
    analysis, app = sample_job_analysis
    ats_report = CareerPilotService.evaluate_ats_for_application(app_id=app.application_id)
    assert isinstance(ats_report, ATSReport)
    assert ats_report.components is not None
    assert len(ats_report.components) >= 5
    assert ats_report.semantic_alignment is not None
    assert ats_report.experience_alignment is not None
    assert ats_report.formatting is not None


def test_interview_prep_action(sample_job_analysis):
    """Verify interview preparation generation, questions, answers, and study roadmap."""
    analysis, app = sample_job_analysis
    prep_state = CareerPilotService.prepare_interview_for_application(
        app_id=app.application_id,
        roadmap_days=7,
    )
    assert isinstance(prep_state, dict)
    assert "questions" in prep_state
    assert len(prep_state["questions"]) > 0
    assert "answers" in prep_state
    assert "roadmap" in prep_state


def test_mock_interview_lifecycle(sample_job_analysis):
    """Verify end-to-end interactive mock session: start, answer submission, hint, follow-up, and finish."""
    analysis, app = sample_job_analysis
    
    # 1. Start Session
    state = CareerPilotService.start_mock_interview_for_application(
        app_id=app.application_id,
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
        persona=InterviewerPersona.SENIOR_ENGINEER,
        feedback_mode=FeedbackMode.COACHING_MODE,
        total_questions=3,
    )
    session_id = state["session_id"]
    assert session_id is not None
    assert len(state["turns"]) == 1

    # 2. Submit Turn 1 Answer with Hint
    evaluation = CareerPilotService.submit_mock_answer(
        session_id=session_id,
        answer_text="We used Apache Airflow to orchestrate ETL pipelines and BigQuery partitioned tables to reduce costs by 25%.",
        hint_used=HintMode.SMALL_HINT,
    )
    assert isinstance(evaluation, AnswerEvaluation)
    assert evaluation.overall_turn_score > 0.0

    # 3. Continue Session to Turn 2
    next_turn, is_finished = CareerPilotService.continue_mock_session(session_id)
    assert next_turn is not None
    assert not is_finished

    # 4. Submit Turn 2 Answer ("I Don't Know")
    evaluation_2 = CareerPilotService.submit_mock_answer(
        session_id=session_id,
        answer_text="I don't know the exact internal implementation details.",
        hint_used=HintMode.NO_HINT,
    )
    assert evaluation_2.is_i_dont_know is True

    # 5. Finish Interview Session
    final_report = CareerPilotService.finish_mock_interview(session_id)
    assert isinstance(final_report, FinalInterviewReport)
    assert final_report.overall_score >= 0.0
    assert len(final_report.topic_mastery) > 0


def test_skill_gap_generation():
    """Verify cross-application skill gap analytics generation."""
    skill_summary = CareerPilotService.get_skill_gaps_summary()
    assert hasattr(skill_summary, "top_missing_skills")
    assert hasattr(skill_summary, "top_demanded_skills")
    assert hasattr(skill_summary, "priority_learning_topics")


def test_negative_cases_and_error_handling():
    """Verify that invalid inputs and missing entities fail gracefully with clear messages."""
    # 1. Non-existent application lookup
    app = CareerPilotService.get_application("app_non_existent_9999")
    assert app is None

    # 2. Invalid application ID for resume generation raises ValueError
    with pytest.raises(ValueError, match="not found"):
        CareerPilotService.generate_resume_for_application("app_invalid_0000")

    # 3. Invalid application ID for ATS evaluation raises ValueError
    with pytest.raises(ValueError, match="not found"):
        CareerPilotService.evaluate_ats_for_application("app_invalid_0000")
