from pathlib import Path
from typing import Union, Optional, List, Dict, Any
from pydantic import BaseModel, Field
import pymupdf  # PyMuPDF / fitz
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class PDFValidationResult(BaseModel):
    """Deterministic ATS format and text extractability audit result for a generated PDF."""
    status: str = "PASS"  # PASS, WARNING, FAIL
    file_path: str
    file_size_bytes: int = 0
    page_count: int = 0
    total_characters: int = 0
    total_words: int = 0
    extracted_text: str = ""
    candidate_name_detected: bool = True
    sections_detected: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    formatting_findings: List[str] = Field(default_factory=list)
    is_searchable: bool = True
    is_single_column: bool = True


class PDFValidator:
    """
    Deterministic validator for ATS-compliant PDF resumes.
    Verifies selectable text, heading presence, single-column flow, and searchability.
    """

    CORE_SECTIONS = [
        "PROFESSIONAL SUMMARY",
        "TECHNICAL SKILLS",
        "PROFESSIONAL EXPERIENCE",
        "KEY PROJECTS",
        "EDUCATION",
    ]

    @classmethod
    def validate_pdf(
        cls,
        file_path: Union[str, Path],
        candidate_name: Optional[str] = None,
        expected_sections: Optional[List[str]] = None,
    ) -> PDFValidationResult:
        path = Path(file_path)
        if not path.exists():
            return PDFValidationResult(
                status="FAIL",
                file_path=str(path),
                formatting_findings=[f"File not found: {path}"],
                candidate_name_detected=False,
                is_searchable=False,
            )

        file_size = path.stat().st_size
        if file_size == 0:
            return PDFValidationResult(
                status="FAIL",
                file_path=str(path),
                file_size_bytes=0,
                formatting_findings=["PDF file is empty (0 bytes)."],
                candidate_name_detected=False,
                is_searchable=False,
            )

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            return PDFValidationResult(
                status="FAIL",
                file_path=str(path),
                file_size_bytes=file_size,
                formatting_findings=[f"Failed to open PDF: {str(e)}"],
                candidate_name_detected=False,
                is_searchable=False,
            )

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            return PDFValidationResult(
                status="FAIL",
                file_path=str(path),
                file_size_bytes=file_size,
                page_count=0,
                formatting_findings=["PDF has 0 pages."],
                candidate_name_detected=False,
                is_searchable=False,
            )

        # Extract text across all pages
        full_text_list = []
        is_single_column = True
        findings = []

        for page_idx, page in enumerate(doc):
            page_text = page.get_text("text")
            full_text_list.append(page_text)

            # Analyze text layout blocks for multi-column detection
            blocks = page.get_text("blocks")
            # blocks: list of (x0, y0, x1, y1, "text", block_no, block_type)
            text_blocks = [b for b in blocks if len(b) >= 5 and b[4].strip() and b[6] == 0]
            
            # If two significant text blocks share significant vertical overlap and split page horizontally
            for i in range(len(text_blocks)):
                for j in range(i + 1, len(text_blocks)):
                    b1, b2 = text_blocks[i], text_blocks[j]
                    # Check if b1 and b2 are side-by-side columns (horizontal separation with vertical overlap)
                    v_overlap = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
                    h_gap = abs(b1[0] - b2[0])
                    if v_overlap > 100 and h_gap > 180 and b1[2] < b2[0]:
                        is_single_column = False
                        findings.append(f"Page {page_idx + 1}: Multi-column layout pattern detected.")

        doc.close()

        extracted_text = "\n".join(full_text_list).strip()
        total_chars = len(extracted_text)
        total_words = len(extracted_text.split())

        if total_chars < 50:
            return PDFValidationResult(
                status="FAIL",
                file_path=str(path),
                file_size_bytes=file_size,
                page_count=page_count,
                total_characters=total_chars,
                total_words=total_words,
                extracted_text=extracted_text,
                formatting_findings=["PDF contains negligible or non-extractable text."],
                candidate_name_detected=False,
                is_searchable=False,
            )

        # Check Candidate Name
        name_detected = True
        if candidate_name:
            # Check individual name parts (e.g. "Trupti", "Kularkar")
            name_parts = candidate_name.split()
            if not all(part.lower() in extracted_text.lower() for part in name_parts):
                name_detected = False
                findings.append(f"Candidate name '{candidate_name}' not fully found in extracted text.")

        # Check Core Sections
        sections_to_check = expected_sections or cls.CORE_SECTIONS
        upper_text = extracted_text.upper()
        detected_sections = []
        missing_sections = []

        for sec in sections_to_check:
            sec_upper = sec.upper()
            if sec_upper in upper_text or sec_upper.replace(" ", "") in upper_text.replace(" ", ""):
                detected_sections.append(sec)
            else:
                missing_sections.append(sec)

        # Check 1-page budget constraint
        if page_count > 1:
            findings.append(f"Resume page count ({page_count}) exceeds standard 1-page target for early/mid-career candidates.")

        if missing_sections:
            findings.append(f"Missing expected standard section headings: {', '.join(missing_sections)}")


        # Check broken replacement characters (\ufffd)
        if "\ufffd" in extracted_text:
            findings.append("Detected replacement character (\\ufffd) indicating potential encoding issue.")

        # Check searchability
        is_searchable = total_words >= 20 and total_chars >= 100

        # Determine Overall Status
        if not name_detected or len(detected_sections) < 2 or not is_searchable:
            overall_status = "FAIL"
        elif missing_sections or not is_single_column or findings:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        return PDFValidationResult(
            status=overall_status,
            file_path=str(path),
            file_size_bytes=file_size,
            page_count=page_count,
            total_characters=total_chars,
            total_words=total_words,
            extracted_text=extracted_text,
            candidate_name_detected=name_detected,
            sections_detected=detected_sections,
            missing_sections=missing_sections,
            formatting_findings=findings,
            is_searchable=is_searchable,
            is_single_column=is_single_column,
        )
