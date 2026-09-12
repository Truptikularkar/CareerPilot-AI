import pytest
import docx
from pathlib import Path
from careerpilot.generators.resume_markdown import MarkdownResumeExporter
from careerpilot.generators.resume_docx import DocxResumeExporter
from careerpilot.graphs.resume_graph import generate_tailored_resume


def test_markdown_and_docx_generation(tmp_path):
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    resume = generate_tailored_resume(eval_file)

    # 1. Test Markdown Exporter
    md = MarkdownResumeExporter.render_markdown(resume)
    assert "# Trupti Kularkar" in md
    assert "## PROFESSIONAL SUMMARY" in md
    assert "## TECHNICAL SKILLS" in md
    assert "## PROFESSIONAL EXPERIENCE" in md
    assert "## KEY PROJECTS" in md
    assert "## EDUCATION" in md

    # 2. Test DOCX Exporter
    docx_path = tmp_path / "test_resume.docx"
    exported_path = DocxResumeExporter.export_docx(resume, docx_path)
    assert exported_path.exists()
    assert exported_path.stat().st_size > 5000  # Valid docx payload

    # Read back docx
    doc = docx.Document(str(exported_path))
    full_doc_text = " ".join(p.text for p in doc.paragraphs)
    assert "Trupti Kularkar" in full_doc_text
    assert "Cognizant" in full_doc_text
    assert "BigQuery" in full_doc_text
