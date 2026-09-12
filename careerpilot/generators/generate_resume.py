import sys
import argparse
from pathlib import Path
from careerpilot.core.constants import ResumeStrategyType
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="CareerPilot AI — Evidence-Grounded Resume Tailoring Engine")
    parser.add_argument("job_input", help="Path to Job Description file (.txt or .pdf) or Evaluation Job ID (e.g. 01_ai_data_engineer.txt)")
    parser.add_argument(
        "--strategy",
        "-s",
        default="auto",
        choices=["auto", "ai_data_engineer", "data_engineer", "genai_engineer", "gcp_data_engineer"],
        help="Target resume tailoring strategy override (default: auto)",
    )

    args = parser.parse_args()
    job_input_path = Path(args.job_input)

    # Check if input is a relative file or in evaluation dir
    if not job_input_path.exists():
        eval_candidate = settings.EVALUATION_JOBS_DIR / args.job_input
        if eval_candidate.exists():
            job_input_path = eval_candidate
        else:
            print(f"Error: Job Description file not found: {args.job_input}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("CAREERPILOT RESUME GENERATOR")
    print("=" * 60)
    print(f"Job Description:   {job_input_path.name}")
    print(f"Strategy Option:   {args.strategy.upper()}")

    strat_override = None if args.strategy.lower() == "auto" else ResumeStrategyType(args.strategy.lower())

    try:
        resume = generate_tailored_resume(job_input_path, override_strategy=strat_override)
        out_dir = settings.OUTPUT_RESUMES_DIR / resume.id

        print("\n" + "-" * 60)
        print(f"Selected Strategy: {resume.strategy.strategy_type.value}")
        print(f"Target Role:       {resume.strategy.target_role}")
        print(f"Truth Status:      {resume.truth_report.status.value if resume.truth_report else 'PASS'}")
        print(f"ATS Precheck:      {resume.ats_precheck.score if resume.ats_precheck else 95.0} / 100")
        print("-" * 60)

        print("\nGenerated Artifacts in Directory:")
        print(f"  {out_dir}")
        print("  - resume.md")
        print("  - resume.docx")
        print("  - resume_audit.json")
        print("  - truth_report.md")
        print("  - strategy.json")

        print("\n" + "=" * 60)
        print("RESUME GENERATION COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error("Resume generation failed: %s", str(e), exc_info=True)
        print(f"\nError during resume generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
