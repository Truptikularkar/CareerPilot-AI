import pytest
from pathlib import Path
from careerpilot.core.config import settings
from careerpilot.parsers.candidate_parser import CandidateParser
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.graphs.interview_prep_graph import prepare_interview
from careerpilot.interview.mock_service import MockInterviewService
from careerpilot.core.constants import (
    ResumeStrategyType,
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    DecisionRecommendation,
    TruthValidationStatus,
)


def test_full_careerpilot_end_to_end_workflow():
    """
    Executes the complete, unabridged CareerPilot AI workflow across all 10 milestones:
    Candidate Load -> JD Parse -> Role Analysis -> Evidence RAG -> Fit Score ->
    Application -> Resume Tailoring -> Truth Guard -> ATS -> Interview Prep ->
    Mock Session -> Adaptive Follow-up -> Final Report.
    """
    # 1. Candidate Source-of-Truth Loading
    profile = CandidateParser.parse_all()
    assert profile.full_name is not None
    assert len(profile.atomic_evidence) > 0

    # 2. Parse Job Description
    job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    jd = JobDescriptionParser.parse_file(job_file)
    assert jd.raw_text is not None

    # 3. LangGraph Job Analysis & Fit Scoring
    analysis = analyze_job(job_file)
    assert analysis.job_id is not None
    assert analysis.fit_score.overall_score > 0.0
    assert analysis.role_classification.primary_role is not None
    assert analysis.seniority_detection.detected_seniority is not None
    assert analysis.recommendation in (
        DecisionRecommendation.APPLY,
        DecisionRecommendation.REVIEW,
        DecisionRecommendation.SKIP,
    )

    # 4. Tailor Resume via LangGraph
    resume = generate_tailored_resume(analysis, override_strategy=ResumeStrategyType.AI_DATA_ENGINEER)
    assert resume.id is not None
    assert len(resume.experiences) > 0
    assert len(resume.projects) > 0

    # 5. Truth Guard Validation
    assert resume.truth_report is not None
    assert resume.truth_report.status == TruthValidationStatus.PASS
    assert resume.truth_report.verified_claims_count > 0

    # 6. ATS Compatibility Evaluation
    ats_report = ATSEvaluator.evaluate_resume(resume, analysis)
    assert ats_report.overall_score >= 80.0
    assert ats_report.keyword_alignment is not None
    assert ats_report.keyword_alignment.score > 0.0
    assert ats_report.semantic_alignment is not None
    assert ats_report.formatting is not None

    # 7. Interview Preparation Engine
    interview_plan = prepare_interview(job_file, days=7)
    assert interview_plan.prep_id is not None
    assert len(interview_plan.questions) > 0
    assert len(interview_plan.answers) > 0
    assert len(interview_plan.star_answers) > 0
    assert len(interview_plan.system_designs) > 0
    assert interview_plan.roadmap is not None
    assert len(interview_plan.roadmap.daily_schedule) == 7

    # 8. Adaptive Mock Interview Agent
    state = MockInterviewService.start_session(
        job_input=job_file,
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
        persona=InterviewerPersona.SENIOR_ENGINEER,
        total_questions=3,
    )
    session_id = state["session_id"]
    assert session_id is not None

    # Turn 1: Submit Grounded Answer
    eval_1 = MockInterviewService.submit_answer(
        session_id=session_id,
        candidate_answer="At Cognizant, I built BigQuery ETL pipelines and automated Airflow DAGs to reduce query costs by 25%.",
        hint_used=HintMode.NO_HINT,
    )
    assert eval_1.overall_turn_score > 0.0

    # Turn 2: Advance & Submit Answer
    turn_2, is_finished = MockInterviewService.continue_session(session_id)
    assert turn_2 is not None
    assert not is_finished
    eval_2 = MockInterviewService.submit_answer(
        session_id=session_id,
        candidate_answer="We implemented partitioned tables and clustered keys to optimize query scan volume.",
    )
    assert eval_2.overall_turn_score > 0.0

    # Finish Mock Session
    final_report = MockInterviewService.finish_session(session_id)
    assert final_report.overall_score >= 0.0
    assert final_report.technical_score >= 0.0
    assert final_report.communication_score >= 0.0
    assert len(final_report.topic_mastery) > 0
