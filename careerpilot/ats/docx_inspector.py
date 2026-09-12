from pathlib import Path
from typing import List, Dict, Any, Union, Set
import docx
from docx.shared import Inches
from careerpilot.core.constants import FormattingRiskType, RiskSeverity
from careerpilot.models.ats import FormattingRiskItem
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class DocxInspector:
    """
    Inspects Microsoft Word (.docx) files to detect ATS parsing pitfalls,
    including layout tables, text placed in headers/footers, multi-column setups, and font anomalies.
    """

    ALLOWED_ATS_FONTS = {"calibri", "arial", "times new roman", "georgia", "garamond", "helvetica", "tahoma", "verdana"}

    @classmethod
    def inspect_docx(cls, docx_path: Union[str, Path]) -> Dict[str, Any]:
        path = Path(docx_path)
        if not path.exists():
            return {
                "file_exists": False,
                "error": f"File not found: {path}",
                "formatting_risks": [],
            }

        try:
            doc = docx.Document(str(path))
        except Exception as e:
            return {
                "file_exists": True,
                "error": f"Could not parse docx: {e}",
                "formatting_risks": [
                    FormattingRiskItem(
                        risk_type=FormattingRiskType.GENERAL,
                        severity=RiskSeverity.HIGH,
                        description=f"Corrupted or non-standard DOCX structure: {e}",
                        location="File Structure",
                        recommendation="Regenerate DOCX using clean standard Word exporter.",
                    )
                ],
            }

        risks: List[FormattingRiskItem] = []
        fonts_found: Set[str] = set()

        # 1. Table Trap Check
        table_count = len(doc.tables)
        if table_count > 0:
            risks.append(
                FormattingRiskItem(
                    risk_type=FormattingRiskType.TABLE_LAYOUT,
                    severity=RiskSeverity.HIGH,
                    description=f"Document contains {table_count} table(s). Many legacy ATS systems cannot parse multi-cell tables linearly.",
                    location="Document Body",
                    recommendation="Remove tables and use single-column linear text with standard bullet formatting.",
                )
            )

        # 2. Header / Footer Inspection
        header_text = ""
        footer_text = ""
        for section in doc.sections:
            if section.header:
                for p in section.header.paragraphs:
                    header_text += p.text.strip() + " "
            if section.footer:
                for p in section.footer.paragraphs:
                    footer_text += p.text.strip() + " "

        if len(header_text.strip()) > 5:
            risks.append(
                FormattingRiskItem(
                    risk_type=FormattingRiskType.HEADER_FOOTER_CONTENT,
                    severity=RiskSeverity.MEDIUM,
                    description="Text detected inside DOCX Header region. Some ATS parsers skip header/footer content completely.",
                    location="DOCX Header",
                    recommendation="Place all contact details and skills directly in the main document body.",
                )
            )

        # 3. Typography & Font Consistency
        paragraph_count = len(doc.paragraphs)
        for p in doc.paragraphs:
            for run in p.runs:
                if run.font.name:
                    fonts_found.add(run.font.name.lower())

        unusual_fonts = [f for f in fonts_found if f not in cls.ALLOWED_ATS_FONTS]
        if unusual_fonts:
            risks.append(
                FormattingRiskItem(
                    risk_type=FormattingRiskType.UNUSUAL_FONT,
                    severity=RiskSeverity.LOW,
                    description=f"Detected non-standard font(s): {', '.join(unusual_fonts)}.",
                    location="Typography",
                    recommendation=f"Use standard ATS-safe fonts (Calibri, Arial, Times New Roman).",
                )
            )

        # 4. Margins Check
        margins_ok = True
        for section in doc.sections:
            if section.left_margin and section.left_margin < Inches(0.4):
                margins_ok = False
                risks.append(
                    FormattingRiskItem(
                        risk_type=FormattingRiskType.SUSPICIOUS_SPACING,
                        severity=RiskSeverity.LOW,
                        description="Document margins are narrower than 0.4 inches, which may cause clipping.",
                        location="Page Setup",
                        recommendation="Set margins between 0.5 and 0.75 inches for optimal ATS and human readability.",
                    )
                )

        return {
            "file_exists": True,
            "paragraph_count": paragraph_count,
            "table_count": table_count,
            "fonts_detected": list(fonts_found),
            "header_has_content": bool(header_text.strip()),
            "footer_has_content": bool(footer_text.strip()),
            "margins_ok": margins_ok,
            "formatting_risks": risks,
        }
