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
    FeedbackMode,
    HintMode,
)


def test_complete_end_to_end_orchestration_workflow():
    """
    Comprehensive, deterministic end-to-end integration test verifying that IDs
    and states connect correctly across every single milestone stage.
    """
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")

    # =========================================================================
    # STAGE 1: Job Description Input & Analysis (Milestones 2 & 3)
    # =========================================================================
    analysis, app = CareerPilotService.analyze_job(
        input_source=eval_file,
        company_name="Snowflake Inc.",
        job_title="Senior AI Data Infrastructure Engineer",
        job_location="San Francisco / Remote",
        job_url="https://snowflake.com/careers/ai_data_eng_101",
    )

    assert analysis.job_id.startswith("job_")
    assert app.application_id.startswith("app_")
    assert app.job_id == analysis.job_id
    assert app.company == "Snowflake Inc."
    assert app.fit_score >= 70.0
    assert app.system_recommendation in (DecisionRecommendation.APPLY, DecisionRecommendation.REVIEW)

    # =========================================================================
    # STAGE 2: Decision Management (User Override)
    # =========================================================================
    app_decided = CareerPilotService.update_application_decision(
        app_id=app.application_id,
        user_decision=DecisionRecommendation.APPLY,
    )
    assert app_decided.user_decision == DecisionRecommendation.APPLY
    assert app_decided.system_recommendation == app.system_recommendation

    # =========================================================================
    # STAGE 3: Resume Tailoring & Versioning (Milestone 4)
    # =========================================================================
    resume_v1, ats_rep_v1, app_v1 = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.AI_DATA_ENGINEER,
    )
    assert resume_v1.id.startswith("resume_")
    assert app_v1.resume_id == resume_v1.id
    assert len(app_v1.resume_versions) == 1
    assert app_v1.resume_versions[0].version_tag == "v1.0"
    assert app_v1.application_status == ApplicationStatus.APPLYING

    # Generate version 2 (with strategy override)
    resume_v2, ats_rep_v2, app_v2 = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.GENAI_ENGINEER,
    )
    assert len(app_v2.resume_versions) == 2
    assert app_v2.resume_versions[1].version_tag == "v2.0"
    assert app_v2.resume_versions[1].strategy_type == "GENAI_ENGINEER"

    # =========================================================================
    # STAGE 4: ATS Compatibility Evaluation (Milestone 5)
    # =========================================================================
    ats_report = CareerPilotService.evaluate_ats_for_application(app.application_id)
    assert ats_report.overall_score >= 75.0
    assert ats_report.job_id == analysis.job_id
    assert len(ats_report.coverage_matrix) > 0
    assert ats_report.must_have_coverage_ratio != ""


    # =========================================================================
    # STAGE 5: Application Status Transition to APPLIED
    # =========================================================================
    app_applied = CareerPilotService.update_application_status(
        app_id=app.application_id,
        new_status=ApplicationStatus.APPLIED,
        notes="Submitted application via Workday portal.",
    )
    assert app_applied.application_status == ApplicationStatus.APPLIED
    assert app_applied.date_applied is not None
    assert any("Workday portal" in n for n in app_applied.notes)

    # =========================================================================
    # STAGE 6: Interview Preparation & Roadmap (Milestone 6)
    # =========================================================================
    prep_state = CareerPilotService.prepare_interview_for_application(
        app_id=app.application_id,
        roadmap_days=7,
    )
    assert len(prep_state.get("questions", [])) >= 15
    assert len(prep_state.get("answers", [])) >= 15
    assert len(prep_state.get("star_answers", [])) >= 3
    assert len(prep_state.get("system_designs", [])) >= 1


    app_prepped = CareerPilotService.get_application(app.application_id)
    assert app_prepped.interview_prep_id is not None
    assert app_prepped.interview_status == "Prepared"

    # =========================================================================
    # STAGE 7: Adaptive Multi-Turn Mock Interview (Milestone 7)
    # =========================================================================
    mock_state = CareerPilotService.start_mock_interview_for_application(
        app_id=app.application_id,
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
        persona=InterviewerPersona.SENIOR_ENGINEER,
        feedback_mode=FeedbackMode.COACHING_MODE,
        total_questions=2,
    )
    mock_session_id = mock_state["session_id"]
    assert mock_session_id.startswith("session_")
    assert len(mock_state["turns"]) == 1

    # Candidate Turn 1 Answer
    eval1 = CareerPilotService.submit_mock_answer(
        session_id=mock_session_id,
        answer_text="At Cognizant, I built BigQuery ingestion pipelines with table partitioning to achieve ~25% query cost savings.",
        hint_used=HintMode.NO_HINT,
    )
    assert eval1.overall_turn_score >= 70.0
    assert len(eval1.truth_checks) == 0

    # Advance to Turn 2
    turn2, is_finished = CareerPilotService.continue_mock_session(mock_session_id)
    assert not is_finished
    assert turn2 is not None

    # Candidate Turn 2 Answer
    eval2 = CareerPilotService.submit_mock_answer(
        session_id=mock_session_id,
        answer_text="I automated Airflow transient failure triage with Google Gemini API, reducing incident response time by ~60%.",
    )
    assert eval2.overall_turn_score >= 50.0

    # Finish Mock Session
    final_report = CareerPilotService.finish_mock_interview(mock_session_id)
    assert final_report.total_turns == 2
    assert final_report.overall_score >= 60.0
    assert final_report.experience_accuracy_score == 100.0


    # =========================================================================
    # STAGE 8: Dashboard & Skill Gap Metrics Integration
    # =========================================================================
    dashboard_kpis = CareerPilotService.get_dashboard_metrics()
    assert dashboard_kpis.total_jobs_analyzed >= 1
    assert dashboard_kpis.applications_submitted >= 1
    assert dashboard_kpis.mock_interviews_completed >= 1

    skill_gaps = CareerPilotService.get_skill_gaps_summary()
    assert len(skill_gaps.top_missing_skills) >= 1
    assert len(skill_gaps.top_demanded_skills) >= 1
    assert len(skill_gaps.priority_learning_topics) >= 1
