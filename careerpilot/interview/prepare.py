import sys
import argparse
from pathlib import Path
from careerpilot.core.config import settings
from careerpilot.graphs.interview_prep_graph import prepare_interview
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="CareerPilot AI — Evidence-Grounded Interview Preparation & Question Engine")
    parser.add_argument("--job", "-j", required=True, help="Path to target Job Description file (.txt) or evaluation job filename")
    parser.add_argument("--strategy", "-s", default="auto", help="Resume/Role strategy (auto, ai_data_engineer, data_engineer, genai_engineer, gcp_data_engineer)")
    parser.add_argument("--difficulty", "-d", default="mixed", help="Target difficulty level (easy, medium, hard, expert, mixed)")
    parser.add_argument("--questions", "-q", type=int, default=35, help="Approximate target question count")
    parser.add_argument("--days", type=int, default=7, help="Study roadmap duration in days (1, 3, 7, 14)")

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

    print("\n" + "=" * 60)
    print("CAREERPILOT INTERVIEW PREPARATION")
    print("=" * 60)
    print(f"Job Description:   {job_path.name}")
    print(f"Target Strategy:   {args.strategy.upper()}")
    print(f"Roadmap Duration:  {args.days} Days")

    # 2. Run LangGraph Preparation Graph
    plan = prepare_interview(job_input=job_path, strategy=args.strategy, days=args.days)

    out_dir = settings.OUTPUT_INTERVIEW_DIR / plan.prep_id

    # 3. Terminal Summary Output
    print("\n" + "-" * 60)
    print(f"Target Role:       {plan.target_role}")
    print(f"Overall Readiness: {plan.readiness_score.overall_readiness}%")
    print(f"Technical Match:   {plan.readiness_score.technical_readiness}%")
    print(f"Resume Confidence: {plan.readiness_score.resume_confidence}%")
    print(f"Project Depth:     {plan.readiness_score.project_confidence}%")
    print(f"Cloud Gap Ready:   {plan.readiness_score.gap_readiness}%")
    print(f"System Design:     {plan.readiness_score.system_design_readiness}%")
    print(f"Behavioral STAR:   {plan.readiness_score.behavioral_readiness}%")
    print(f"Truth Status:      {plan.truth_report.get('status', 'PASS') if plan.truth_report else 'PASS'}")
    print("-" * 60)

    print(f"\nCRITICAL TOPICS ({len(plan.questions)} Questions Total):")
    for q in [q for q in plan.questions if q.priority.value == "CRITICAL"][:4]:
        print(f"  * [{q.category.value}] {q.question}")

    print(f"\nSAMPLE TECHNICAL QUESTIONS:")
    for q in [q for q in plan.questions if q.category.value in ("BIGQUERY", "AIRFLOW", "RAG", "GCP", "JD_TECHNICAL")][:3]:
        print(f"  * [{q.category.value}] {q.question}")

    print(f"\nSAMPLE PROJECT DEEP-DIVES:")
    for q in [q for q in plan.questions if q.category.value == "PROJECT_DEEP_DIVE"][:2]:
        print(f"  * {q.question}")

    print(f"\nBEHAVIORAL STAR SCENARIOS:")
    for s in plan.star_answers[:2]:
        q_match = next((q for q in plan.questions if q.question_id == s.question_id), None)
        q_txt = q_match.question if q_match else "Behavioral Question"
        print(f"  * {q_txt}")
        print(f"    Action: {s.action[:120]}...")
        print(f"    Result: {s.result}")

    print(f"\nSYSTEM DESIGN CHALLENGES ({len(plan.system_designs)} Scenarios):")
    for sd in plan.system_designs:
        print(f"  * {sd.title}")

    print(f"\nEXPERIENCE GAPS & TRANSFERABILITY:")
    for q in [q for q in plan.questions if q.category.value == "EXPERIENCE_GAP"][:2]:
        print(f"  * {q.question}")

    print(f"\n{args.days}-DAY STUDY ROADMAP:")
    for day in plan.roadmap.daily_schedule[:3]:
        print(f"  * {day.title} -> {day.focus_areas[0] if day.focus_areas else ''}")
    if len(plan.roadmap.daily_schedule) > 3:
        print(f"  * ... ({len(plan.roadmap.daily_schedule) - 3} more days in roadmap.json / readiness_report.md)")

    print("\nGenerated Preparation Artifacts:")
    print(f"  Directory: {out_dir}")
    print("  - interview_plan.json / interview_plan.md")
    print("  - questions.json / questions.md")
    print("  - answers.json / answers.md")
    print("  - system_design.json")
    print("  - roadmap.json")
    print("  - readiness_report.md")
    print("  - truth_report.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
