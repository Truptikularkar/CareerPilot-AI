import sys
from pathlib import Path
from typing import Optional
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.models.job import JobAnalysisResult
from careerpilot.core.constants import RequirementImportance


def format_analysis_report(result: JobAnalysisResult) -> str:
    """Formats JobAnalysisResult into a clean, professional CLI report."""
    role_info = result.role_classification
    reality = result.role_reality
    fit = result.fit_score
    cloud = result.cloud_transferability

    must_haves = [r.normalized_skill for r in result.requirements if r.importance == RequirementImportance.MUST_HAVE]
    nice_to_haves = [r.normalized_skill for r in result.requirements if r.importance == RequirementImportance.NICE_TO_HAVE]

    work_dist = ", ".join(f"{k}: {v}%" for k, v in reality.work_distribution.items())

    lines = [
        "=" * 60,
        "CAREERPILOT JOB ANALYSIS",
        "=" * 60,
        f"Company:        {result.company_name}",
        f"Job Title:      {result.job_title}",
        "",
        "ROLE CLASSIFICATION:",
        f"  Primary:      {role_info.primary_role.value}",
        f"  Secondary:    {role_info.secondary_role.value if role_info.secondary_role else 'None'}",
        f"  Seniority:    {role_info.seniority.value} ({result.seniority_detection.explicit_years_required or 'Standard'} yrs required)",
        "",
        f"ROLE REALITY (Day-to-day Work Split):",
        f"  {work_dist}",
        f"  Primary Type: {reality.primary_work_type}",
        "",
        f"FIT SCORE:       {fit.total_weighted_score:.1f} / 100",
        f"RECOMMENDATION:  [{result.recommendation.value}]",
        "",
        "MUST-HAVE REQUIREMENTS:",
    ]

    for mh in must_haves or ["General engineering qualifications"]:
        status_icon = "[+]" if mh in result.key_strengths else "[-]"
        lines.append(f"  {status_icon} {mh}")

    lines.append("")
    lines.append("NICE-TO-HAVE SKILLS:")
    for nh in nice_to_haves or ["None specified"]:
        status_icon = "[+]" if nh in result.key_strengths else "[ ]"
        lines.append(f"  {status_icon} {nh}")

    lines.append("")
    lines.append("CANDIDATE VERIFIED STRENGTHS:")
    for s in result.key_strengths[:8] or ["None"]:
        lines.append(f"  * {s}")

    lines.append("")
    lines.append("IDENTIFIED SKILL GAPS:")
    for g in result.key_gaps[:6] or ["None detected"]:
        lines.append(f"  * {g}")

    lines.append("")
    lines.append("RISK ASSESSMENT:")
    if result.risks:
        for r in result.risks:
            lines.append(f"  * [{r.severity.value}] {r.description}")
            if r.mitigation:
                lines.append(f"      Mitigation: {r.mitigation}")
    else:
        lines.append("  * No significant risks detected.")

    lines.append("")
    lines.append("CLOUD TRANSFERABILITY:")
    lines.append(f"  * Status: {cloud.transferability_status.value}")
    lines.append(f"  * Details: {cloud.transferability_reasoning}")


    lines.append("")
    lines.append("REASONING & DECISION FACTOR:")
    for r_line in result.explainable_reasoning.splitlines():
        lines.append(f"  {r_line}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main(file_path: Optional[str] = None):
    target = file_path or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not target:
        default_jd = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
        if not default_jd.exists():
            default_jd = Path("data/sample/sample_jds/ai_engineer_jd.txt")
        target = str(default_jd)

    print(f"\nAnalyzing Job Description: {target}\n")
    analysis = analyze_job(target)
    print(format_analysis_report(analysis))


if __name__ == "__main__":
    main()
