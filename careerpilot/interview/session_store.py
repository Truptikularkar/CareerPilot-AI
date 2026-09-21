import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from careerpilot.core.config import settings
from careerpilot.core.constants import MockInterviewMode, InterviewDifficulty, InterviewerPersona, SessionStatus
from careerpilot.db.session import get_db
from careerpilot.db.schema import MockSessionDB
from careerpilot.models.mock_interview import (
    MockInterviewTurn,
    AnswerEvaluation,
    FinalInterviewReport,
    TopicMastery,
    WeaknessItem,
    StrengthItem,
)
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class SessionStore:
    """
    Persists interactive mock interview sessions to SQLite and local JSON files,
    allowing live turns to be recorded, paused, resumed, and exported as final artifacts.
    """

    @classmethod
    def create_session(
        cls,
        session_id: str,
        job_id: str,
        target_role: str,
        mode: MockInterviewMode = MockInterviewMode.FULL_INTERVIEW,
        difficulty: InterviewDifficulty = InterviewDifficulty.ADAPTIVE,
        persona: InterviewerPersona = InterviewerPersona.SENIOR_ENGINEER,
        candidate_id: Optional[str] = None,
    ) -> MockSessionDB:
        cid = candidate_id or settings.active_candidate_id
        with get_db() as db:
            existing = db.query(MockSessionDB).filter(MockSessionDB.id == session_id).first()
            if existing:
                return existing

            db_session = MockSessionDB(
                id=session_id,
                job_id=job_id,
                candidate_id=cid,
                target_role=target_role,
                current_difficulty=difficulty.value,
                turns_json=[],
                readiness_json={
                    "mode": mode.value,
                    "difficulty": difficulty.value,
                    "persona": persona.value,
                    "status": SessionStatus.IN_PROGRESS.value,
                },
                is_completed=False,
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            logger.info("Created new MockSessionDB: %s (Role: %s)", session_id, target_role)
            return db_session

    @classmethod
    def save_turn(cls, session_id: str, turn: MockInterviewTurn):
        with get_db() as db:
            db_session = db.query(MockSessionDB).filter(MockSessionDB.id == session_id).first()
            if not db_session:
                logger.warning("MockSessionDB '%s' not found for save_turn.", session_id)
                return

            turns_list = list(db_session.turns_json) if db_session.turns_json else []
            # Check if turn already recorded
            existing_idx = next((i for i, t in enumerate(turns_list) if t.get("turn_id") == turn.turn_id), None)
            if existing_idx is not None:
                turns_list[existing_idx] = turn.model_dump()
            else:
                turns_list.append(turn.model_dump())

            db_session.turns_json = turns_list
            db.commit()
            logger.debug("Saved turn %d for session '%s'.", turn.turn_number, session_id)

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as db:
            db_session = db.query(MockSessionDB).filter(MockSessionDB.id == session_id).first()
            if not db_session:
                return None
            return {
                "id": db_session.id,
                "job_id": db_session.job_id,
                "candidate_id": db_session.candidate_id,
                "target_role": db_session.target_role,
                "current_difficulty": db_session.current_difficulty,
                "turns": db_session.turns_json or [],
                "readiness": db_session.readiness_json or {},
                "is_completed": db_session.is_completed,
                "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
            }

    @classmethod
    def complete_session(cls, session_id: str, report: FinalInterviewReport):
        with get_db() as db:
            db_session = db.query(MockSessionDB).filter(MockSessionDB.id == session_id).first()
            if db_session:
                db_session.is_completed = True
                curr_readiness = dict(db_session.readiness_json or {})
                curr_readiness["status"] = SessionStatus.COMPLETED.value
                curr_readiness["final_report"] = report.model_dump()
                db_session.readiness_json = curr_readiness
                db.commit()
                logger.info("Marked MockSessionDB '%s' as COMPLETED.", session_id)

    @classmethod
    def export_session_artifacts(
        cls,
        session_id: str,
        turns: List[MockInterviewTurn],
        report: FinalInterviewReport,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        out = Path(output_dir) if output_dir else (settings.OUTPUT_MOCK_SESSIONS_DIR / session_id)
        out.mkdir(parents=True, exist_ok=True)
        files: Dict[str, Path] = {}

        # 1. session.json
        s_json = out / "session.json"
        with open(s_json, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": session_id,
                "job_id": report.job_id,
                "target_role": report.target_role,
                "mode": report.mode.value,
                "persona": report.persona.value,
                "total_turns": len(turns),
                "overall_score": report.overall_score,
                "turns": [t.model_dump() for t in turns],
            }, f, indent=2)
        files["session.json"] = s_json

        # 2. transcript.md
        tr_md = out / "transcript.md"
        tr_lines = [
            f"# Mock Interview Transcript — Session `{session_id}`",
            f"**Target Role:** `{report.target_role}` | **Mode:** `{report.mode.value}` | **Persona:** `{report.persona.value}`",
            f"**Overall Score:** `{report.overall_score}%` | **Total Turns:** `{len(turns)}`",
            "",
            "---",
            "",
        ]
        for t in turns:
            score_str = f"{t.evaluation.overall_turn_score}%" if t.evaluation else "Pending"
            tr_lines.extend([
                f"### Turn {t.turn_number}: [{t.category}] {t.question_text}",
                f"**Topic:** `{t.topic}` | **Difficulty:** `{t.difficulty}` | **Follow-up Depth:** `{t.followup_depth}`",
                "",
                f"**Candidate Answer:**",
                f"> {t.candidate_answer if t.candidate_answer else '*(No answer provided)*'}",
                "",
                f"**Turn Score:** `{score_str}`",
            ])
            if t.evaluation:
                tr_lines.extend([
                    f"**Feedback:** {t.evaluation.feedback}",
                    f"**Coaching Tip:** *\"{t.evaluation.coaching_tip}\"*",
                ])
            tr_lines.extend(["", "---", ""])

        with open(tr_md, "w", encoding="utf-8") as f:
            f.write("\n".join(tr_lines))
        files["transcript.md"] = tr_md

        # 3. evaluation.json
        ev_json = out / "evaluation.json"
        with open(ev_json, "w", encoding="utf-8") as f:
            json.dump([t.evaluation.model_dump() for t in turns if t.evaluation], f, indent=2)
        files["evaluation.json"] = ev_json

        # 4. feedback.md
        fb_md = out / "feedback.md"
        fb_lines = [
            f"# Real-Time Coaching Feedback & Turn-by-Turn Analysis",
            f"**Session:** `{session_id}` | **Target Role:** `{report.target_role}`",
            "",
        ]
        for t in turns:
            if t.evaluation:
                fb_lines.extend([
                    f"### Turn {t.turn_number}: {t.question_text}",
                    f"- **Score:** {t.evaluation.overall_turn_score}%",
                    f"- **Strengths:** {', '.join(t.evaluation.strengths_observed) if t.evaluation.strengths_observed else 'None'}",
                    f"- **Weaknesses:** {', '.join(t.evaluation.weaknesses_observed) if t.evaluation.weaknesses_observed else 'None'}",
                    f"- **Coaching Advice:** {t.evaluation.coaching_tip}",
                    "",
                ])
        with open(fb_md, "w", encoding="utf-8") as f:
            f.write("\n".join(fb_lines))
        files["feedback.md"] = fb_md

        # 5. weaknesses.json
        wk_json = out / "weaknesses.json"
        with open(wk_json, "w", encoding="utf-8") as f:
            json.dump([w.model_dump() for w in report.weaknesses], f, indent=2)
        files["weaknesses.json"] = wk_json

        # 6. topic_scores.json
        ts_json = out / "topic_scores.json"
        with open(ts_json, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in report.topic_mastery.items()}, f, indent=2)
        files["topic_scores.json"] = ts_json

        # 7. final_report.md
        fr_md = out / "final_report.md"
        fr_lines = [
            f"# Comprehensive Mock Interview Performance Report",
            f"**Session ID:** `{session_id}` | **Target Role:** `{report.target_role}` | **Mode:** `{report.mode.value}`",
            "",
            f"## **Overall Mock Interview Score: {report.overall_score}%**",
            "",
            "### Performance Sub-Scores",
            "| Evaluation Dimension | Score | Assessment Level |",
            "| :--- | :--- | :--- |",
            f"| **Technical Correctness & Depth** | {report.technical_score}% | {'High' if report.technical_score >= 80 else 'Developing'} |",
            f"| **Communication, Clarity & Structure** | {report.communication_score}% | {'High' if report.communication_score >= 80 else 'Developing'} |",
            f"| **Resume Knowledge & Evidence Grounding** | {report.resume_knowledge_score}% | {'High' if report.resume_knowledge_score >= 80 else 'Developing'} |",
            f"| **Project Depth & Ownership** | {report.project_score}% | {'High' if report.project_score >= 80 else 'Developing'} |",
            f"| **System Design & Architecture** | {report.system_design_score}% | {'High' if report.system_design_score >= 80 else 'Developing'} |",
            f"| **Behavioral STAR Storytelling** | {report.behavioral_score}% | {'High' if report.behavioral_score >= 80 else 'Developing'} |",
            f"| **Problem Solving & Follow-ups** | {report.problem_solving_score}% | {'High' if report.problem_solving_score >= 80 else 'Developing'} |",
            f"| **Experience Accuracy & Truth Guard** | {report.experience_accuracy_score}% | {'100% Truthful' if report.experience_accuracy_score == 100 else 'Penalized for unverified claims'} |",
            "",
            "### Topic Mastery Breakdown",
            "| Topic | Score (0-5) | Questions Asked | Mastery Status |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for top, m in report.topic_mastery.items():
            fr_lines.append(f"| **{top}** | `{m.mastery_score}/5.0` | {m.questions_asked} | **{m.status}** |")

        fr_lines.extend([
            "",
            "### Candidate Strengths",
        ])
        for s in report.strengths:
            fr_lines.append(f"- **{s.topic}:** {s.description}")

        fr_lines.extend([
            "",
            "### Areas for Improvement & Weakness Detection",
        ])
        for w in report.weaknesses:
            fr_lines.append(f"- **{w.topic}:** {w.description} -> *Remedy: {w.suggested_remedy}*")

        fr_lines.extend([
            "",
            "### Recommended Preparation Roadmap",
        ])
        for rec in report.recommended_study_topics:
            fr_lines.append(f"1. {rec}")

        fr_lines.extend([
            "",
            f"**Recommended Next Mock Session:** `{report.recommended_next_mock_mode.value}`",
        ])

        with open(fr_md, "w", encoding="utf-8") as f:
            f.write("\n".join(fr_lines))
        files["final_report.md"] = fr_md

        return files
