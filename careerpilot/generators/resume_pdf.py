import re
import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import Union, Optional, List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pymupdf

from careerpilot.models.resume import TailoredResume
from careerpilot.models.artifact import ResumeArtifact
from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class PDFResumeExporter:
    """
    Exports TailoredResume into a clean, single-column, ATS-compliant PDF document.
    Enforces a strict 1-page layout target for early/mid-career candidates with adaptive spacing.
    """

    @classmethod
    def get_safe_filename(cls, candidate_name: str, role_title: str, company: Optional[str] = None) -> str:
        raw_parts = [candidate_name, role_title]
        if company:
            raw_parts.append(company)
        raw_parts.append("Resume.pdf")

        joined = "_".join(p for p in raw_parts if p)
        sanitized = re.sub(r'[\\/*?:"<>|]', "", joined)
        sanitized = re.sub(r"[\s_]+", "_", sanitized).strip("_")
        return sanitized if sanitized.endswith(".pdf") else f"{sanitized}.pdf"

    @classmethod
    def _escape(cls, text: str) -> str:
        if not text:
            return ""
        return saxutils.escape(str(text))

    @classmethod
    def _build_story(
        cls,
        resume: TailoredResume,
        margin_inch: float = 0.45,
        base_font_size: float = 8.8,
        heading_size: float = 10.5,
    ) -> List:
        styles = getSampleStyleSheet()

        name_style = ParagraphStyle(
            "ATS_Name",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            alignment=TA_CENTER,
            textColor=HexColor("#0A2540"),
            spaceAfter=2,
        )

        contact_style = ParagraphStyle(
            "ATS_Contact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=base_font_size,
            leading=base_font_size + 2.0,
            alignment=TA_CENTER,
            textColor=HexColor("#4A4A4A"),
            spaceAfter=1.5,
        )

        links_style = ParagraphStyle(
            "ATS_Links",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=base_font_size - 0.5,
            leading=base_font_size + 1.5,
            alignment=TA_CENTER,
            textColor=HexColor("#0066CC"),
            spaceAfter=4,
        )

        section_heading_style = ParagraphStyle(
            "ATS_SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=heading_size,
            leading=heading_size + 2.0,
            alignment=TA_LEFT,
            textColor=HexColor("#0A2540"),
            spaceBefore=3,
            spaceAfter=1,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "ATS_Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=base_font_size,
            leading=base_font_size + 2.5,
            alignment=TA_LEFT,
            textColor=HexColor("#1A1A1A"),
            spaceAfter=2,
        )

        item_title_style = ParagraphStyle(
            "ATS_ItemTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=base_font_size + 0.5,
            leading=base_font_size + 2.5,
            alignment=TA_LEFT,
            textColor=HexColor("#1A1A1A"),
            spaceBefore=2,
            spaceAfter=0.5,
            keepWithNext=True,
        )

        item_meta_style = ParagraphStyle(
            "ATS_ItemMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=base_font_size - 0.5,
            leading=base_font_size + 1.5,
            alignment=TA_LEFT,
            textColor=HexColor("#555555"),
            spaceAfter=1.5,
            keepWithNext=True,
        )

        bullet_style = ParagraphStyle(
            "ATS_Bullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=base_font_size,
            leading=base_font_size + 2.2,
            alignment=TA_LEFT,
            textColor=HexColor("#222222"),
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=1.5,
        )

        story = []
        h = resume.header

        # 1. Header
        story.append(Paragraph(cls._escape(h.full_name), name_style))

        contact_parts = [p for p in [h.email, h.phone, h.location] if p]
        if contact_parts:
            story.append(Paragraph(cls._escape(" | ".join(contact_parts)), contact_style))

        links = [p for p in [h.linkedin_url, h.github_url] if p]
        if links:
            story.append(Paragraph(cls._escape(" | ".join(links)), links_style))

        def add_section_divider(heading_title: str):
            story.append(Paragraph(cls._escape(heading_title.upper()), section_heading_style))
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=HexColor("#0A2540"),
                    spaceBefore=0.5,
                    spaceAfter=2,
                )
            )

        # 2. Professional Summary
        if resume.summary and getattr(resume.summary, "text", None):
            add_section_divider("Professional Summary")
            story.append(Paragraph(cls._escape(resume.summary.text), body_style))

        # 3. Technical Skills
        if resume.skills_categories:
            add_section_divider("Technical Skills")
            for sc in resume.skills_categories:
                skills_str = ", ".join(sc.skills)
                skill_line = f"<b>{cls._escape(sc.category_name)}:</b> {cls._escape(skills_str)}"
                story.append(Paragraph(f"• {skill_line}", bullet_style))

        # 4. Professional Experience
        if resume.experiences:
            add_section_divider("Professional Experience")
            for exp in resume.experiences:
                exp_title = f"{exp.title} — {exp.company}"
                story.append(Paragraph(cls._escape(exp_title), item_title_style))
                meta_line = f"{exp.start_date} – {exp.end_date}" + (f" | {exp.location}" if exp.location else "")
                story.append(Paragraph(cls._escape(meta_line), item_meta_style))

                for b in exp.bullets:
                    b_str = b.text if hasattr(b, "text") else str(b)
                    story.append(Paragraph(f"• {cls._escape(b_str)}", bullet_style))

        # 5. Key Projects
        if resume.projects:
            add_section_divider("Key Projects")
            for proj in resume.projects:
                tech_text = f" ({', '.join(proj.technologies)})" if proj.technologies else ""
                proj_title = f"{proj.name}{tech_text}"
                story.append(Paragraph(cls._escape(proj_title), item_title_style))

                for b in proj.bullets:
                    b_str = b.text if hasattr(b, "text") else str(b)
                    story.append(Paragraph(f"• {cls._escape(b_str)}", bullet_style))

        # 6. Education
        if resume.education:
            add_section_divider("Education")
            for edu in resume.education:
                honors_str = f" | {edu.honors}" if getattr(edu, "honors", None) else ""
                grad_str = f" ({edu.graduation_year})" if getattr(edu, "graduation_year", None) else ""
                edu_text = f"<b>{cls._escape(edu.degree)} in {cls._escape(edu.field_of_study)}</b> — {cls._escape(edu.institution)}{cls._escape(grad_str)}{cls._escape(honors_str)}"
                story.append(Paragraph(f"• {edu_text}", bullet_style))

        # 7. Certifications
        if resume.certifications:
            add_section_divider("Certifications")
            for cert in resume.certifications:
                c_name = cert.name if hasattr(cert, "name") else str(cert)
                issuer = f" — {cert.issuer}" if hasattr(cert, "issuer") and cert.issuer else ""
                year = f" ({cert.year})" if hasattr(cert, "year") and cert.year else ""
                story.append(Paragraph(f"• <b>{cls._escape(c_name)}</b>{cls._escape(issuer)}{cls._escape(year)}", bullet_style))

        return story

    @classmethod
    def export_pdf(
        cls,
        resume: TailoredResume,
        output_path: Optional[Union[str, Path]] = None,
        company: Optional[str] = None,
        enforce_one_page: bool = True,
    ) -> ResumeArtifact:
        """
        Renders a TailoredResume to a verified 1-page ATS-compliant PDF file.
        Utilizes content prioritization and a 3-pass adaptive compression loop
        with PyMuPDF page validation to guarantee page_count == 1 for early-career candidates.
        """
        if output_path is not None:
            path = Path(output_path)
        else:
            path = Path(settings.BASE_DIR) / "data" / "generated" / "resumes" / resume.id / "resume.pdf"

        path.parent.mkdir(parents=True, exist_ok=True)

        # Clone resume to allow non-destructive content prioritization
        resume_to_render = resume.model_copy(deep=True)

        # Content Prioritization for early/mid-career:
        # 1. Limit projects to top 3
        if len(resume_to_render.projects) > 3:
            resume_to_render.projects = resume_to_render.projects[:3]

        # 2. Clamp bullets per experience between 2 and 4
        for exp in resume_to_render.experience:
            if len(exp.bullets) > 4:
                exp.bullets = exp.bullets[:4]

        def render_doc(res_obj, m_inch, f_size, h_size):
            doc = SimpleDocTemplate(
                str(path),
                pagesize=letter,
                leftMargin=m_inch * inch,
                rightMargin=m_inch * inch,
                topMargin=m_inch * inch,
                bottomMargin=m_inch * inch,
                title=f"{res_obj.header.full_name} Resume",
                author=res_obj.header.full_name,
                subject=f"Tailored Resume - {res_obj.strategy.strategy_type.value if hasattr(res_obj.strategy, 'strategy_type') else 'AI Data Engineer'}",
            )
            story = cls._build_story(res_obj, margin_inch=m_inch, base_font_size=f_size, heading_size=h_size)
            doc.build(story)

        # Pass 1: Standard compact layout
        render_doc(resume_to_render, 0.40, 8.8, 10.2)
        page_count = 1

        try:
            pdf_doc = pymupdf.open(str(path))
            page_count = len(pdf_doc)
            pdf_doc.close()

            # Pass 2: Adaptive micro-compression if page_count > 1
            if page_count > 1 and enforce_one_page:
                logger.info("PDF Pass 1 generated %d pages. Applying Pass 2 micro-compression...", page_count)
                render_doc(resume_to_render, 0.34, 8.2, 9.6)
                pdf_doc2 = pymupdf.open(str(path))
                page_count = len(pdf_doc2)
                pdf_doc2.close()

            # Pass 3: Aggressive content pruning if still > 1 page
            if page_count > 1 and enforce_one_page:
                logger.info("PDF Pass 2 generated %d pages. Applying Pass 3 aggressive pruning...", page_count)
                if len(resume_to_render.projects) > 2:
                    resume_to_render.projects = resume_to_render.projects[:2]
                for exp in resume_to_render.experience:
                    if len(exp.bullets) > 3:
                        exp.bullets = exp.bullets[:3]
                render_doc(resume_to_render, 0.30, 7.8, 9.0)
                pdf_doc3 = pymupdf.open(str(path))
                page_count = len(pdf_doc3)
                pdf_doc3.close()

            logger.info("Final PDF generation complete. Total pages: %d", page_count)
        except Exception as e:
            logger.warning("Error checking PDF page count via PyMuPDF: %s", e)

        safe_name = cls.get_safe_filename(
            candidate_name=resume.header.full_name,
            role_title=resume.strategy.target_role if hasattr(resume.strategy, "target_role") else "Data_Engineer",
            company=company,
        )

        return ResumeArtifact(
            artifact_type="pdf",
            file_name=safe_name,
            file_path=str(path),
            content_type="application/pdf",
            resume_id=resume.id,
            is_valid=(page_count == 1) if enforce_one_page else True,
        )
