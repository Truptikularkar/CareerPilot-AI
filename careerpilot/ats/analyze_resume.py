import sys
import argparse
import json
from pathlib import Path
from careerpilot.core.config import settings
from careerpilot.models.resume import TailoredResume
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.ats.report_exporter import ATSReportExporter
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="CareerPilot AI — ATS Compatibility & Deep Resume Optimization Engine")
    parser.add_argument("resume_input", help="Path to tailored resume (.md or .docx) or generated resume directory/id")
    parser.add_argument("--job", "-j", required=True, help="Path to target Job Description file (.txt or .pdf) or Evaluation Job ID")

    args = parser.parse_args()

    # 1. Resolve Job Description
    job_path = Path(args.job)
    if not job_path.exists():
        eval_job = settings.EVALUATION_JOBS_DIR / args.job
        if eval_job.exists():
            job_path = eval_job
        else:
            print(f"Error: Target Job Description not found: {args.job}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("CAREERPILOT ATS COMPATIBILITY ANALYSIS")
    print("=" * 60)
    print(f"Job Description:   {job_path.name}")
    print(f"Resume Input:      {args.resume_input}")

    # Analyze Job
    analysis = analyze_job(job_path)

    # 2. Resolve Resume
    resume_path = Path(args.resume_input)
    docx_file = None

    if resume_path.is_dir():
        docx_cand = resume_path / "resume.docx"
        if docx_cand.exists():
            docx_file = docx_cand
        # Generate or load tailored resume
        resume = generate_tailored_resume(analysis)
    elif resume_path.is_file():
        if resume_path.suffix.lower() == ".docx":
            docx_file = resume_path
        resume = generate_tailored_resume(analysis)
    else:
        # Check generated resumes folder by ID
        gen_dir = settings.OUTPUT_RESUMES_DIR / args.resume_input
        if gen_dir.exists():
            docx_cand = gen_dir / "resume.docx"
            if docx_cand.exists():
                docx_file = docx_cand
            resume = generate_tailored_resume(analysis)
        else:
            resume = generate_tailored_resume(analysis)

    # 3. Run ATS Evaluation
    report = ATSEvaluator.evaluate_resume(resume, analysis, docx_path=docx_file)

    # 4. Export ATS Report
    out_dir = settings.OUTPUT_RESUMES_DIR / resume.id
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = ATSReportExporter.export_json(report, out_dir / "ats_report.json")
    md_path = ATSReportExporter.export_markdown(report, out_dir / "ats_report.md")

    # 5. Output Summary to Terminal
    print("\n" + "-" * 60)
    print(f"Target Strategy:               {report.target_strategy}")
    print(f"ATS-Style Compatibility Score: {report.overall_score} / 100 ({report.score_interpretation})")
    print(f"Keyword & Requirement Match:   {report.components['keyword_coverage'].score} / 100")
    print(f"Skill Taxonomy Alignment:      {report.components['skill_taxonomy'].score} / 100")
    print(f"Semantic Role Alignment:       {report.components['semantic_alignment'].score} / 100")
    print(f"Experience & Tenure Alignment: {report.components['experience_alignment'].score} / 100")
    print(f"Resume Structure Score:        {report.components['structure'].score} / 100")
    print(f"Formatting Compatibility:      {report.components['formatting'].score} / 100")
    print(f"Readability Score:             {report.components['readability'].score} / 100")
    print(f"Truth Guard Status:            {report.truth_status.value}")
    print(f"Must-Have Coverage:            {report.must_have_coverage_ratio}")
    print(f"Nice-To-Have Coverage:         {report.nice_to_have_coverage_ratio}")
    print("-" * 60)

    if report.missing_requirements:
        print("\nMissing Requirements & Recommendations:")
        for mr in report.missing_requirements[:4]:
            print(f"  * {mr.requirement} ({mr.importance.value}): {mr.recommendation}")

    if report.suggestions:
        print("\nActionable Optimization Recommendations:")
        for s in report.suggestions[:4]:
            print(f"  * [{s.priority.value}] {s.recommended_action}")

    if report.interview_seed:
        print("\nInterview Preparation Signals (Seed for Milestone 6):")
        print(f"  * High Priority Skills: {', '.join(report.interview_seed.high_priority_skills[:5])}")
        print(f"  * Deep-Dive Topics:     {report.interview_seed.likely_interview_topics[0] if report.interview_seed.likely_interview_topics else 'N/A'}")

    print("\nGenerated ATS Report Files:")
    print(f"  - JSON:     {json_path}")
    print(f"  - Markdown: {md_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
