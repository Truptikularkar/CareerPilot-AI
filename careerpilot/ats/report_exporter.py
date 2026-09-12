import json
from pathlib import Path
from typing import Union
from careerpilot.models.ats import ATSReport


class ATSReportExporter:
    """
    Renders structured ATSReport into both machine-readable JSON and human-readable Markdown.
    """

    @classmethod
    def export_json(cls, report: ATSReport, output_path: Union[str, Path]) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        return path

    @classmethod
    def render_markdown(cls, report: ATSReport) -> str:
        lines = [
            f"# ATS Compatibility & Resume Optimization Report",
            f"**Resume ID:** `{report.resume_id}` | **Job:** `{report.job_title}` ({report.company_name or 'Target Employer'})",
            f"**Target Strategy:** `{report.target_strategy}` | **Truth Status:** `{report.truth_status.value}`",
            "",
            "## 1. ATS-Style Compatibility Score",
            f"### **Overall Score: {report.overall_score} / 100** ({report.score_interpretation})",
            "",
            "| Component | Score | Weight | Weighted Score | Details |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for key, comp in report.components.items():
            lines.append(f"| **{comp.name}** | {comp.score}/100 | {int(comp.weight * 100)}% | {comp.weighted_score} | {comp.explanation} |")

        lines.extend([
            "",
            "## 2. Requirement Coverage Summary",
            f"- **Must-Have Coverage:** `{report.must_have_coverage_ratio}`",
            f"- **Nice-To-Have Coverage:** `{report.nice_to_have_coverage_ratio}`",
            "",
            "### Requirement Traceability Matrix",
            "| Requirement | Importance | Match Level | Resume Evidence | Candidate Truth Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for item in report.coverage_matrix:
            res_ev = item.resume_evidence or "Omitted in draft"
            lines.append(f"| **{item.requirement}** | {item.importance.value} | `{item.match_level.value}` | {res_ev} | {item.truth_status} |")

        if report.missing_requirements:
            lines.extend([
                "",
                "## 3. Missing Requirements & Truth-Grounded Recommendations",
            ])
            for mr in report.missing_requirements:
                lines.append(f"- **{mr.requirement}** (`{mr.importance.value}`): {mr.explanation}")
                lines.append(f"  *Recommendation:* {mr.recommendation}")

        if report.formatting_risks:
            lines.extend([
                "",
                "## 4. ATS Layout & Formatting Risks",
            ])
            for fr in report.formatting_risks:
                lines.append(f"- [{fr.severity.value}] **{fr.risk_type.value}** ({fr.location}): {fr.description}")
                lines.append(f"  *Fix:* {fr.recommendation}")
        else:
            lines.extend([
                "",
                "## 4. ATS Layout & Formatting Risks",
                "- No significant layout traps, column issues, or unparseable tables detected. Single-column linear layout verified.",
            ])

        lines.extend([
            "",
            "## 5. Actionable Optimization Recommendations",
        ])
        for s in report.suggestions:
            lines.append(f"- **[{s.priority.value}] {s.category}:** {s.recommended_action}")
            lines.append(f"  *Reason:* {s.reason}")

        if report.interview_seed:
            seed = report.interview_seed
            lines.extend([
                "",
                "## 6. Interview Preparation Signals (Seed for Milestone 6)",
                f"- **High-Priority Technical Topics:** {', '.join(seed.high_priority_skills)}",
                f"- **Candidate Verified Strengths:** {', '.join(seed.candidate_strengths)}",
                f"- **Candidate Gaps / Pivot Points:** {', '.join(seed.candidate_gaps) if seed.candidate_gaps else 'None'}",
                "",
                "### Core Technical Deep-Dive Focus Areas",
            ])
            for topic in seed.likely_interview_topics:
                lines.append(f"  * {topic}")
            lines.append("")
            lines.append("### Likely Challenged Resume Claims")
            for claim in seed.challenged_claims:
                lines.append(f"  * {claim}")

        return "\n".join(lines)

    @classmethod
    def export_markdown(cls, report: ATSReport, output_path: Union[str, Path]) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = cls.render_markdown(report)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
