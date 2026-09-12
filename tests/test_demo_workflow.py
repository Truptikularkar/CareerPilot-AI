import pytest
from pathlib import Path
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
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.core.config import settings


def test_synthetic_demo_candidate_full_workflow():
    """
    Deterministic end-to-end integration test verifying that CareerPilot AI
    operates smoothly on synthetic demo candidate data (Alex Rivera) without
    any reliance on private personal files.
    """
    demo_dir = Path("data/demo")
    assert (demo_dir / "profile.yaml").exists()
    assert (demo_dir / "experience.md").exists()
    assert (demo_dir / "projects.md").exists()

    cand_store = CandidateStore()
    try:
        # Index synthetic demo candidate
        cand_store.index_candidate_data(candidate_dir=demo_dir, clear_existing=True)

        # 1. Analyze Job Description
        eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
        analysis, app = CareerPilotService.analyze_job(
            input_source=eval_file,
            company_name="CloudScale Analytics",
            job_title="Senior AI Data Platform Engineer",
        )

        assert analysis.job_id.startswith("job_")
        assert app.application_id.startswith("app_")
        assert app.fit_score >= 70.0
        assert app.system_recommendation in (DecisionRecommendation.APPLY, DecisionRecommendation.REVIEW)

        # 2. Resume Tailoring & Truth Guard
        resume, ats_rep, app_v1 = CareerPilotService.generate_resume_for_application(
            app_id=app.application_id,
            strategy=ResumeStrategyType.AI_DATA_ENGINEER,
        )
        assert resume.id.startswith("resume_")
        assert resume.truth_validation is not None
        assert resume.truth_validation.status.value == "PASS"
        assert len(app_v1.resume_versions) == 1

        # 3. ATS Compatibility Evaluation
        ats_report = CareerPilotService.evaluate_ats_for_application(app.application_id)
        assert ats_report.overall_score >= 70.0
        assert len(ats_report.coverage_matrix) > 0

        # 4. Interview Preparation Pipeline
        prep_state = CareerPilotService.prepare_interview_for_application(
            app_id=app.application_id,
            roadmap_days=3,
        )
        assert len(prep_state.get("questions", [])) >= 15
        assert len(prep_state.get("star_answers", [])) >= 3

        # 5. Adaptive Mock Interview Simulation
        mock_state = CareerPilotService.start_mock_interview_for_application(
            app_id=app.application_id,
            mode=MockInterviewMode.TECHNICAL_ONLY,
            difficulty=InterviewDifficulty.MEDIUM,
            persona=InterviewerPersona.SENIOR_ENGINEER,
            feedback_mode=FeedbackMode.COACHING_MODE,
            total_questions=2,
        )
        mock_session_id = mock_state["session_id"]
        assert mock_session_id.startswith("session_")

        eval1 = CareerPilotService.submit_mock_answer(
            session_id=mock_session_id,
            answer_text="At Apex Cloud Solutions, I designed and optimized automated ETL pipelines in BigQuery and Airflow processing 2.5M+ daily records.",
            hint_used=HintMode.NO_HINT,
        )
        assert eval1.overall_turn_score >= 60.0

        final_report = CareerPilotService.finish_mock_interview(mock_session_id)
        assert final_report.overall_score >= 60.0
        assert final_report.experience_accuracy_score == 100.0
    finally:
        # Restore verified candidate index for subsequent tests
        cand_dir = Path("data/candidate")
        if cand_dir.exists() and (cand_dir / "profile.yaml").exists():
            cand_store.index_candidate_data(candidate_dir=cand_dir, clear_existing=True)

