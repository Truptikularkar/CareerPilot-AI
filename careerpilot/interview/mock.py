import sys
import argparse
from pathlib import Path
from careerpilot.core.config import settings
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
)
from careerpilot.interview.mock_service import MockInterviewService
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


def parse_mode(mode_str: str) -> MockInterviewMode:
    mode_map = {
        "full": MockInterviewMode.FULL_INTERVIEW,
        "technical": MockInterviewMode.TECHNICAL_ONLY,
        "resume": MockInterviewMode.RESUME_DEEP_DIVE,
        "project": MockInterviewMode.PROJECT_DEEP_DIVE,
        "system_design": MockInterviewMode.SYSTEM_DESIGN,
        "behavioral": MockInterviewMode.BEHAVIORAL,
        "genai": MockInterviewMode.GENAI_RAG,
        "data_engineering": MockInterviewMode.DATA_ENGINEERING,
        "gcp": MockInterviewMode.GCP_CLOUD,
        "weakness": MockInterviewMode.WEAKNESS_FOCUS,
    }
    return mode_map.get(mode_str.lower(), MockInterviewMode.FULL_INTERVIEW)


def parse_difficulty(diff_str: str) -> InterviewDifficulty:
    diff_map = {
        "adaptive": InterviewDifficulty.ADAPTIVE,
        "easy": InterviewDifficulty.EASY,
        "medium": InterviewDifficulty.MEDIUM,
        "hard": InterviewDifficulty.HARD,
        "expert": InterviewDifficulty.EXPERT,
    }
    return diff_map.get(diff_str.lower(), InterviewDifficulty.ADAPTIVE)


def parse_persona(persona_str: str) -> InterviewerPersona:
    p_map = {
        "senior_engineer": InterviewerPersona.SENIOR_ENGINEER,
        "technical_engineer": InterviewerPersona.TECHNICAL_ENGINEER,
        "recruiter": InterviewerPersona.RECRUITER,
        "ai_engineer": InterviewerPersona.AI_ENGINEER,
        "data_engineer": InterviewerPersona.DATA_ENGINEER,
        "cloud_engineer": InterviewerPersona.CLOUD_ENGINEER,
        "hiring_manager": InterviewerPersona.HIRING_MANAGER,
    }
    return p_map.get(persona_str.lower(), InterviewerPersona.SENIOR_ENGINEER)


def main():
    parser = argparse.ArgumentParser(description="CareerPilot AI — Interactive Adaptive Mock Interview Agent")
    parser.add_argument("--job", "-j", required=True, help="Path to target Job Description file (.txt) or evaluation job filename")
    parser.add_argument("--mode", "-m", default="full", help="Interview mode (full, technical, resume, project, system_design, behavioral, genai, data_engineering, gcp, weakness)")
    parser.add_argument("--difficulty", "-d", default="adaptive", help="Difficulty mode (adaptive, easy, medium, hard, expert)")
    parser.add_argument("--persona", "-p", default="senior_engineer", help="Interviewer persona (senior_engineer, recruiter, ai_engineer, data_engineer, cloud_engineer, hiring_manager)")
    parser.add_argument("--coaching", "-c", action="store_true", help="Enable immediate coaching feedback after every answer")
    parser.add_argument("--questions", "-q", type=int, default=6, help="Total questions planned")

    args = parser.parse_args()

    # 1. Resolve Job Description
    job_path = Path(args.job)
    if not job_path.exists():
        eval_job = settings.EVALUATION_JOBS_DIR / args.job
        if eval_job.exists():
            job_path = eval_job
        else:
            print(f"Error: Job description file not found: {args.job}")
            sys.exit(1)

    mode = parse_mode(args.mode)
    diff = parse_difficulty(args.difficulty)
    persona = parse_persona(args.persona)
    fb_mode = FeedbackMode.COACHING_MODE if args.coaching else FeedbackMode.INTERVIEW_MODE

    print("\n" + "=" * 65)
    print("CAREERPILOT AI — ADAPTIVE MOCK INTERVIEW AGENT")
    print("=" * 65)
    print(f"Target Job:     {job_path.name}")
    print(f"Interview Mode: {mode.value}")
    print(f"Difficulty:     {diff.value}")
    print(f"Persona:        {persona.value}")
    print(f"Feedback Mode:  {fb_mode.value}")
    print(f"Questions:      {args.questions} Planned")
    print("-" * 65)
    print("Tips: Type your answer and press Enter.")
    print("Commands: '/hint' for a small hint | '/fullhint' for full hint | '/idk' for I don't know | '/quit' to end early.")
    print("=" * 65 + "\n")

    # 2. Start Session
    state = MockInterviewService.start_session(
        job_input=job_path,
        mode=mode,
        difficulty=diff,
        persona=persona,
        feedback_mode=fb_mode,
        total_questions=args.questions,
    )
    session_id = state["session_id"]

    # 3. Interactive Multi-Turn Loop
    while True:
        curr_turn = state["turns"][-1]
        turn_num = curr_turn.turn_number
        depth_label = f" (Follow-up Level {curr_turn.followup_depth})" if curr_turn.followup_depth > 0 else ""

        print(f"\n[Interviewer — {persona.value}] (Question {turn_num}/{args.questions}{depth_label})")
        print(f"Topic: [{curr_turn.topic}] | Difficulty: [{curr_turn.difficulty}]")
        print(f"\"{curr_turn.question_text}\"\n")

        hint_used = HintMode.NO_HINT
        while True:
            try:
                cand_input = input("Candidate > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession paused/interrupted by user.")
                cand_input = "/quit"

            if cand_input == "/hint":
                hint_used = HintMode.SMALL_HINT
                print("💡 [Small Hint]: Focus on the underlying architectural mechanism and data flow.")
                continue
            elif cand_input == "/fullhint":
                hint_used = HintMode.FULL_HINT
                print(f"💡 [Full Hint]: Mention: {', '.join(curr_turn.topic.split()[:2])}, measurable impact, and trade-offs.")
                continue
            elif cand_input == "/idk":
                cand_input = "I don't know the exact details of this concept."
                break
            elif cand_input == "/quit":
                print("\nWrapping up interview early and generating performance report...")
                report = MockInterviewService.finish_session(session_id)
                _print_final_report(report, session_id)
                return
            elif not cand_input:
                print("Please enter an answer, '/hint', '/idk', or '/quit'.")
                continue
            else:
                break

        # Submit Answer
        print("\nEvaluating response...")
        evaluation = MockInterviewService.submit_answer(
            session_id=session_id,
            candidate_answer=cand_input,
            hint_used=hint_used,
        )

        # Print Live Coaching Feedback if enabled
        if args.coaching:
            print("\n" + "-" * 50)
            print(f"🎯 Turn Score: {evaluation.overall_turn_score}%")
            if evaluation.correct_concepts:
                print(f"✓ Strong Concepts: {', '.join(evaluation.correct_concepts[:3])}")
            if evaluation.missing_concepts:
                print(f"⚠ Missing Concepts: {', '.join(evaluation.missing_concepts[:2])}")
            if evaluation.truth_checks:
                for tc in evaluation.truth_checks:
                    print(f"🚨 [Truth Warning]: {tc.explanation}")
            print(f"💡 Coaching Advice: {evaluation.coaching_tip}")
            print("-" * 50)

        # Continue or Finish
        next_turn, is_finished = MockInterviewService.continue_session(session_id)
        if is_finished or not next_turn:
            break

    # 4. Final Report Presentation
    report = MockInterviewService.finish_session(session_id)
    _print_final_report(report, session_id)


def _print_final_report(report, session_id: str):
    out_dir = settings.OUTPUT_MOCK_SESSIONS_DIR / session_id
    print("\n" + "=" * 65)
    print("MOCK INTERVIEW FINAL PERFORMANCE REPORT")
    print("=" * 65)
    print(f"Target Role:             {report.target_role}")
    print(f"Total Turns Completed:   {report.total_turns}")
    print(f"Overall Interview Score: {report.overall_score}%")
    print("-" * 65)
    print(f"  * Technical Correctness:    {report.technical_score}%")
    print(f"  * Communication & Clarity:  {report.communication_score}%")
    print(f"  * Resume Evidence Accuracy: {report.resume_knowledge_score}%")
    print(f"  * Problem Solving & Depth:  {report.problem_solving_score}%")
    print(f"  * System Design:            {report.system_design_score}%")
    print(f"  * Behavioral STAR:          {report.behavioral_score}%")
    print(f"  * Experience Truth Guard:   {report.experience_accuracy_score}%")
    print("-" * 65)

    if report.strengths:
        print("\nCANDIDATE STRENGTHS:")
        for s in report.strengths[:3]:
            print(f"  ✓ [{s.topic}] {s.description}")

    if report.weaknesses:
        print("\nAREAS FOR IMPROVEMENT:")
        for w in report.weaknesses[:3]:
            print(f"  ⚠ [{w.topic}] {w.description}")
            print(f"    -> Remedy: {w.suggested_remedy}")

    print("\nRECOMMENDED STUDY ROADMAP:")
    for idx, rec in enumerate(report.recommended_study_topics[:4], 1):
        print(f"  {idx}. {rec}")

    print(f"\nRecommended Next Mock Session: [{report.recommended_next_mock_mode.value}]")
    print(f"\nAll 7 Session Artifacts Exported to:")
    print(f"  Directory: {out_dir}")
    print("  - session.json")
    print("  - transcript.md")
    print("  - evaluation.json")
    print("  - feedback.md")
    print("  - weaknesses.json")
    print("  - topic_scores.json")
    print("  - final_report.md")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
