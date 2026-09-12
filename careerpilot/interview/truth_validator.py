import re
from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import TruthValidationStatus, ClaimType
from careerpilot.models.interview import InterviewAnswer, STARAnswer
from careerpilot.models.resume import TruthClaimCheck, TruthValidationReport
from careerpilot.truth_guard.auditor import TruthAuditor
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class InterviewTruthValidator:
    """
    Validates interview answers and STAR stories to ensure zero hallucination,
    metric immutability, and strict truth preservation.
    """

    @classmethod
    def validate_interview_answers(
        cls,
        answers: List[InterviewAnswer],
        star_answers: List[STARAnswer],
    ) -> TruthValidationReport:
        blocked: List[TruthClaimCheck] = []
        flagged: List[TruthClaimCheck] = []
        verified_count = 0

        # 1. Validate Interview Answers
        for ans in answers:
            full_text = f"{ans.direct_answer} {ans.explanation} {ans.candidate_example} {ans.technical_details} {ans.result_impact}"

            # Audit against TruthAuditor
            report = TruthAuditor.audit_sections({"answer": full_text})
            if report.status == TruthValidationStatus.BLOCK:
                blocked.extend(report.blocked_claims)
            elif report.status == TruthValidationStatus.FLAG:
                flagged.extend(report.flagged_claims)
            else:
                verified_count += 1

        # 2. Validate STAR Answers
        for star in star_answers:
            if star.is_insufficient_evidence:
                verified_count += 1
                continue

            star_text = f"{star.situation} {star.task} {star.action} {star.result} {star.key_takeaway}"
            report_s = TruthAuditor.audit_sections({"star": star_text})
            if report_s.status == TruthValidationStatus.BLOCK:
                blocked.extend(report_s.blocked_claims)
            elif report_s.status == TruthValidationStatus.FLAG:
                flagged.extend(report_s.flagged_claims)
            else:
                verified_count += 1

        final_status = TruthValidationStatus.BLOCK if blocked else (TruthValidationStatus.FLAG if flagged else TruthValidationStatus.PASS)

        return TruthValidationReport(
            status=final_status,
            verified_claims_count=verified_count,
            flagged_claims=flagged,
            blocked_claims=blocked,
            summary_reasoning="All interview answers and STAR stories are 100% grounded in verified candidate truth." if final_status == TruthValidationStatus.PASS else f"Detected {len(blocked)} blocked truth violation(s) in interview answers.",
        )
