import re
from typing import List, Dict, Any
from careerpilot.core.constants import FormattingRiskType, RiskSeverity
from careerpilot.models.ats import FormattingRiskItem
from careerpilot.models.resume import TailoredResume
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class FormattingRulesEngine:
    """
    Simulates ATS layout parsing risks across document structure, character encodings,
    date consistency, and visual layout traps.
    """

    PROHIBITED_CHARS = re.compile(r"[\u2022\u25cf\u25cb\u25a0\u25a1\u2713\u2714\u2716\u2794\u27a4\u2192\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F]")

    @classmethod
    def evaluate_resume_formatting(cls, resume: TailoredResume) -> List[FormattingRiskItem]:
        risks: List[FormattingRiskItem] = []

        # 1. Contact Information Location Check
        h = resume.header
        if not h.email or not h.phone:
            risks.append(
                FormattingRiskItem(
                    risk_type=FormattingRiskType.HEADER_FOOTER_CONTENT,
                    severity=RiskSeverity.HIGH,
                    description="Essential contact details (email or phone) are missing in the main header body.",
                    location="Header",
                    recommendation="Ensure full name, verified email, and phone number appear in the document body header.",
                )
            )

        # 2. Date consistency check
        date_patterns_found = set()
        for exp in resume.experiences:
            date_str = f"{exp.start_date} – {exp.end_date}"
            if re.search(r"\b\d{4}\s*[\-–—]\s*(?:Present|\d{4})\b", date_str, re.IGNORECASE):
                date_patterns_found.add("YYYY - Present")
            elif re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\b", date_str, re.IGNORECASE):
                date_patterns_found.add("Mon YYYY")
            elif re.search(r"\b\d{2}/\d{4}\b", date_str):
                date_patterns_found.add("MM/YYYY")

        if len(date_patterns_found) > 1:
            risks.append(
                FormattingRiskItem(
                    risk_type=FormattingRiskType.INCONSISTENT_DATES,
                    severity=RiskSeverity.LOW,
                    description=f"Multiple date formats detected across experiences: {', '.join(date_patterns_found)}.",
                    location="Professional Experience",
                    recommendation="Standardize all experience and project dates to a uniform format (e.g. 'YYYY – Present' or 'Mon YYYY – Present').",
                )
            )

        # 3. Excessive symbol or special character check
        full_text = f"{resume.summary.text} "
        for e in resume.experiences:
            full_text += " ".join(e.bullets) + " "
        for p in resume.projects:
            full_text += " ".join(p.bullets) + " "

        unusual_chars = cls.PROHIBITED_CHARS.findall(full_text)
        if len(unusual_chars) > 8:
            risks.append(
                FormattingRiskItem(
                    risk_type=FormattingRiskType.EXCESSIVE_SYMBOLS,
                    severity=RiskSeverity.MEDIUM,
                    description=f"Detected {len(unusual_chars)} special symbols or non-standard bullet characters that may fail legacy ATS ASCII text extraction.",
                    location="Document Body",
                    recommendation="Use standard ASCII hyphens (-) or standard list bullet points instead of custom symbols/emojis.",
                )
            )

        return risks
