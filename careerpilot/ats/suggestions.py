from typing import List, Dict, Any
from careerpilot.core.constants import SuggestionPriority, TruthValidationStatus
from careerpilot.models.ats import (
    OptimizationSuggestion,
    MissingRequirement,
    FormattingRiskItem,
)
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume, TruthValidationReport


class OptimizationSuggestionsEngine:
    """
    Generates actionable, truth-grounded resume optimization recommendations.
    Strictly forbids recommending unevidenced technologies or metric inflation.
    """

    @classmethod
    def generate_suggestions(
        cls,
        analysis: JobAnalysisResult,
        resume: TailoredResume,
        missing_reqs: List[MissingRequirement],
        formatting_risks: List[FormattingRiskItem],
        truth_report: Optional[TruthValidationReport] = None,
    ) -> List[OptimizationSuggestion]:
        suggestions: List[OptimizationSuggestion] = []

        # 1. Truth Guard Violations (Highest Priority)
        if truth_report and truth_report.status == TruthValidationStatus.BLOCK:
            for bc in truth_report.blocked_claims:
                suggestions.append(
                    OptimizationSuggestion(
                        priority=SuggestionPriority.CRITICAL,
                        category="Truth Safety",
                        current_state=f"Blocked claim: '{bc.claim_text}'",
                        recommended_action=f"Remove or rephrase ungrounded claim. {bc.violation_reason}",
                        reason="Candidate resumes must contain 100% verified factual claims.",
                        evidence="Candidate ground truth files in data/candidate/",
                    )
                )

        # 2. Missing Requirements & Skill Optimization
        for mr in missing_reqs:
            if "NOT_VERIFIED" in mr.candidate_status:
                suggestions.append(
                    OptimizationSuggestion(
                        priority=SuggestionPriority.MEDIUM if mr.importance.value == "NICE_TO_HAVE" else SuggestionPriority.HIGH,
                        category="Skill Alignment",
                        current_state=f"JD requires '{mr.requirement}', which is unverified in candidate history.",
                        recommended_action=(
                            f"Do NOT add '{mr.requirement}' to your resume. "
                            f"If this is a cloud technology (e.g. AWS/Azure/Redshift), emphasize strong production GCP experience with transferable data architecture patterns."
                            if any(k in mr.requirement.lower() for k in ["aws", "azure", "redshift", "s3", "glue", "emr", "kinesis", "snowflake"])
                            else f"Do not fabricate '{mr.requirement}'. Focus interview talking points on closely related verified competencies."
                        ),

                        reason=f"Candidate evidence has no verified production record for {mr.requirement}.",
                        evidence="Candidate Skills & Experience verification records",
                    )
                )
            elif "VERIFIED_IN_PROFILE" in mr.candidate_status:
                suggestions.append(
                    OptimizationSuggestion(
                        priority=SuggestionPriority.HIGH,
                        category="Keyword Coverage",
                        current_state=f"Candidate has verified evidence for '{mr.requirement}', but it is omitted in current resume draft.",
                        recommended_action=f"Add '{mr.requirement}' to the appropriate Technical Skills category.",
                        reason="Maximizes ATS keyword alignment using strictly verified candidate capabilities.",
                        evidence="Verified candidate profile.yaml",
                    )
                )

        # 3. Section and Bullet Positioning
        strategy_type = resume.strategy.strategy_type.value
        if "AI_DATA_ENGINEER" in strategy_type:
            suggestions.append(
                OptimizationSuggestion(
                    priority=SuggestionPriority.MEDIUM,
                    category="Section Positioning",
                    current_state="AI Data Engineer strategy selected.",
                    recommended_action="Keep 'AI-Driven Data Quality Monitoring' and 'AI AutoHeal Agent' at top of Projects section to showcase dual Data Eng + GenAI capabilities.",
                    reason="Aligns visual focus with the JD's combined data pipeline and autonomous agent requirements.",
                    evidence="projects.md",
                )
            )

        # 4. Formatting Recommendations
        for fr in formatting_risks:
            suggestions.append(
                OptimizationSuggestion(
                    priority=SuggestionPriority.HIGH if fr.severity.value in ("HIGH", "CRITICAL") else SuggestionPriority.LOW,
                    category="ATS Formatting",
                    current_state=fr.description,
                    recommended_action=fr.recommendation,
                    reason=f"Resolves {fr.risk_type.value} risk to guarantee clean ATS text extraction.",
                    evidence="ATS Layout Guidelines",
                )
            )

        return suggestions
