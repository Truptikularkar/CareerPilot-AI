from pathlib import Path
from typing import Optional, Union
from careerpilot.models.resume import TailoredResume
from careerpilot.models.artifact import ResumeArtifact
from careerpilot.generators.resume_pdf import PDFResumeExporter
from careerpilot.core.config import settings


class MarkdownResumeExporter:
    """
    Renders TailoredResume into standard, ATS-friendly Markdown.
    Avoids multi-column layouts, tables, textboxes, or special character icons.
    """

    @classmethod
    def render_markdown(cls, resume: TailoredResume) -> str:
        h = resume.header
        lines = []

        # 1. Header
        lines.append(f"# {h.full_name}")
        contact_parts = [p for p in [h.email, h.phone, h.location] if p]
        lines.append(" | ".join(contact_parts))
        links = [p for p in [h.linkedin_url, h.github_url, h.portfolio_url] if p]
        if links:
            lines.append(" | ".join(links))
        lines.append("")

        # 2. Professional Summary
        lines.append("## PROFESSIONAL SUMMARY")
        lines.append(resume.summary.text)
        lines.append("")

        # 3. Technical Skills
        lines.append("## TECHNICAL SKILLS")
        for sc in resume.skills_categories:
            lines.append(f"- **{sc.category_name}**: {', '.join(sc.skills)}")
        lines.append("")

        # 4. Professional Experience
        lines.append("## PROFESSIONAL EXPERIENCE")
        for exp in resume.experiences:
            lines.append(f"### {exp.title} — {exp.company}")
            loc_str = f" | {exp.location}" if exp.location else ""
            lines.append(f"*{exp.start_date} – {exp.end_date}{loc_str}*")
            lines.append("")
            for b in exp.bullets:
                lines.append(f"- {b}")
            lines.append("")

        # 5. Projects
        lines.append("## KEY PROJECTS")
        for proj in resume.projects:
            tech_str = f" (*Technologies: {', '.join(proj.technologies)}*)" if proj.technologies else ""
            lines.append(f"### {proj.name}{tech_str}")
            if proj.description:
                lines.append(f"*{proj.description}*")
            lines.append("")
            for b in proj.bullets:
                lines.append(f"- {b}")
            lines.append("")

        # 6. Education
        lines.append("## EDUCATION")
        for edu in resume.education:
            lines.append(f"**{edu.degree} in {edu.field_of_study}** | {edu.institution}")
            lines.append(f"Graduated: {edu.graduation_year or '2023'}{f' ({edu.honors})' if edu.honors else ''}")
            lines.append("")

        # 7. Certifications (if any)
        if resume.certifications:
            lines.append("## CERTIFICATIONS & LEARNING")
            for cert in resume.certifications:
                lines.append(f"- **{cert.name}** — {cert.issuer or 'Google Cloud'} ({cert.year or '2024'})")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def export_markdown(
        cls,
        resume: TailoredResume,
        output_path: Optional[Union[str, Path]] = None,
        company: Optional[str] = None,
    ) -> ResumeArtifact:
        """
        Renders markdown and writes to output_path, returning a ResumeArtifact.
        """
        if output_path is not None:
            path = Path(output_path)
        else:
            path = Path(settings.BASE_DIR) / "data" / "generated" / "resumes" / resume.id / "resume.md"

        path.parent.mkdir(parents=True, exist_ok=True)
        content = cls.render_markdown(resume)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        role_name = "Engineer"
        if hasattr(resume, "strategy") and resume.strategy and hasattr(resume.strategy, "strategy_type"):
            role_name = resume.strategy.strategy_type.value

        safe_pdf_name = PDFResumeExporter.get_safe_filename(
            candidate_name=resume.header.full_name,
            role_title=role_name,
            company=company,
        )
        safe_filename = safe_pdf_name.replace(".pdf", ".md")

        return ResumeArtifact(
            artifact_type="markdown",
            file_name=safe_filename,
            file_path=str(path),
            content_type="text/markdown",
            file_bytes=content.encode("utf-8"),
            resume_id=resume.id,
            is_valid=True,
        )

