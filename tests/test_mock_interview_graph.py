import pytest
from pathlib import Path
from careerpilot.core.constants import MockInterviewMode, InterviewDifficulty, InterviewerPersona, FeedbackMode, SessionStatus
from careerpilot.interview.mock_service import MockInterviewService
from careerpilot.graphs.mock_interview_graph import mock_interview_graph


def test_mock_interview_service_multi_turn_flow():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")

    # 1. Start Session
    state = MockInterviewService.start_session(
        job_input=eval_file,
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
        persona=InterviewerPersona.SENIOR_ENGINEER,
        feedback_mode=FeedbackMode.COACHING_MODE,
        total_questions=3,
    )
    session_id = state["session_id"]
    assert state["session_status"] == SessionStatus.IN_PROGRESS
    assert len(state["turns"]) == 1

    # 2. Turn 1 Answer
    ans1 = "I am an AI Data Engineer with 1.9+ years at Cognizant specializing in GCP BigQuery and Airflow pipelines."
    eval1 = MockInterviewService.submit_answer(session_id, ans1)
    assert eval1.overall_turn_score >= 60.0

    # 3. Continue to Turn 2
    turn2, is_finished = MockInterviewService.continue_session(session_id)
    assert not is_finished
    assert turn2 is not None
    assert turn2.turn_number == 2

    # 4. Turn 2 Answer
    ans2 = "At Cognizant, I partitioned and clustered BigQuery tables by date to achieve a verified ~25% cost reduction through partition pruning."
    eval2 = MockInterviewService.submit_answer(session_id, ans2)
    assert eval2.overall_turn_score >= 70.0


    # 5. Continue to Turn 3
    turn3, is_finished = MockInterviewService.continue_session(session_id)
    assert not is_finished
    assert turn3 is not None
    assert turn3.turn_number == 3

    # 6. Turn 3 Answer (triggers completion)
    ans3 = "I built an AI AutoHeal agent using Gemini API that resolved ~75% of Airflow transient errors."
    MockInterviewService.submit_answer(session_id, ans3)

    # 7. Continue past planned limit triggers final report
    next_turn, is_finished = MockInterviewService.continue_session(session_id)
    assert is_finished is True
    assert next_turn is None

    # 8. Verify Report
    report = MockInterviewService.finish_session(session_id)
    assert report is not None
    assert report.total_turns == 3
    assert report.overall_score >= 70.0
    assert report.experience_accuracy_score == 100.0


def test_mock_interview_graph_compilation():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    initial_state = {
        "job_input": eval_file,
        "mode": MockInterviewMode.FULL_INTERVIEW,
        "difficulty": InterviewDifficulty.ADAPTIVE,
        "persona": InterviewerPersona.SENIOR_ENGINEER,
        "total_questions_planned": 2,
    }

    result = mock_interview_graph.invoke(initial_state)
    assert result["session_id"].startswith("session_")
    assert result["current_question"] is not None
