from typing import Dict
from careerpilot.models.resume import TailoredResume, TruthValidationReport
from careerpilot.truth_guard.auditor import TruthAuditor
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class TruthValidator:
    """
    Validates a complete TailoredResume against verified candidate ground truth.
    """

    @classmethod
    def validate_tailored_resume(cls, resume: TailoredResume) -> TruthValidationReport:
        logger.info("TruthValidator: Auditing TailoredResume '%s' against verified evidence...", resume.id)

        # Build section dictionary
        sections: Dict[str, str] = {
            "summary": resume.summary.text,
            "skills": " ".join(", ".join(c.skills) for c in resume.skills_categories),
            "experience": " ".join(" ".join(e.bullets) for e in resume.experiences),
            "projects": " ".join(" ".join(p.bullets) for p in resume.projects),
        }

        report = TruthAuditor.audit_sections(sections)
        logger.info(
            "TruthValidator Report for '%s': Status=%s, Verified Claims=%d, Blocked=%d, Flagged=%d",
            resume.id,
            report.status.value,
            report.verified_claims_count,
            len(report.blocked_claims),
            len(report.flagged_claims),
        )
        return report
