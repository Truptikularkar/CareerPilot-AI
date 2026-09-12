import pytest
import uuid
from pathlib import Path
from careerpilot.core.constants import MockInterviewMode, InterviewDifficulty, InterviewerPersona
from careerpilot.models.mock_interview import MockInterviewTurn, FinalInterviewReport
from careerpilot.interview.session_store import SessionStore


def test_session_store_crud_and_artifacts(tmp_path):
    session_id = f"test_sess_{uuid.uuid4().hex[:8]}"

    # 1. Create Session
    db_sess = SessionStore.create_session(
        session_id=session_id,
        job_id="job_test",
        target_role="AI Data Engineer",
        mode=MockInterviewMode.FULL_INTERVIEW,
        difficulty=InterviewDifficulty.ADAPTIVE,
        persona=InterviewerPersona.SENIOR_ENGINEER,
    )
    assert db_sess is not None
    assert db_sess.id == session_id

    # 2. Save Turn
    turn = MockInterviewTurn(
        turn_id="turn_1",
        turn_number=1,
        question_id="q_1",
        question_text="Explain BigQuery partitioning.",
        category="BIGQUERY",
        topic="BigQuery",
        difficulty="MEDIUM",
        followup_depth=0,
        candidate_answer="Partitioning date blocks reduces byte scans.",
    )
    SessionStore.save_turn(session_id, turn)

    # 3. Retrieve Session
    retrieved = SessionStore.get_session(session_id)
    assert retrieved is not None
    assert len(retrieved["turns"]) == 1
    assert retrieved["turns"][0]["question_id"] == "q_1"

    # 4. Complete Session & Export Artifacts
    report = FinalInterviewReport(
        session_id=session_id,
        job_id="job_test",
        target_role="AI Data Engineer",
        mode=MockInterviewMode.FULL_INTERVIEW,
        persona=InterviewerPersona.SENIOR_ENGINEER,
        total_turns=1,
        overall_score=85.0,
        technical_score=85.0,
        topic_mastery={},
        strengths=[],
        weaknesses=[],
        jd_coverage=[],
        challenging_questions=[],
        questions_answered_well=[],
        questions_answered_poorly=[],
        unsupported_claims=[],
        recommended_study_topics=["Review BigQuery sort keys."],
        executive_summary="Completed test mock session.",
    )
    SessionStore.complete_session(session_id, report)

    files = SessionStore.export_session_artifacts(session_id, [turn], report, output_dir=tmp_path)
    assert len(files) == 7
    assert (tmp_path / "session.json").exists()
    assert (tmp_path / "transcript.md").exists()
    assert (tmp_path / "evaluation.json").exists()
    assert (tmp_path / "feedback.md").exists()
    assert (tmp_path / "weaknesses.json").exists()
    assert (tmp_path / "topic_scores.json").exists()
    assert (tmp_path / "final_report.md").exists()
