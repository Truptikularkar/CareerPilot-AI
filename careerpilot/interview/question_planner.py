from typing import Dict, Any, List
from careerpilot.core.constants import QuestionCategory, QuestionPriority, DifficultyLevel
from careerpilot.models.ats import InterviewReadinessSeed
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class QuestionPlanner:
    """
    Plans interview question quotas and category allocations
    tailored to the target role, JD requirements, and candidate gaps.
    """

    @classmethod
    def plan_question_distribution(
        cls,
        analysis: JobAnalysisResult,
        seed: InterviewReadinessSeed,
        resume: TailoredResume,
        total_questions: int = 35,
    ) -> Dict[QuestionCategory, int]:
        strategy_type = resume.strategy.strategy_type.value

        # Base distribution
        quotas: Dict[QuestionCategory, int] = {
            QuestionCategory.HR_SCREENING: 3,
            QuestionCategory.RESUME_WALKTHROUGH: 2,
            QuestionCategory.JD_TECHNICAL: 8,
            QuestionCategory.RESUME_DEEP_DIVE: 6,
            QuestionCategory.PROJECT_DEEP_DIVE: 5,
            QuestionCategory.SCENARIO_BASED: 4,
            QuestionCategory.SYSTEM_DESIGN: 2,
            QuestionCategory.BEHAVIORAL: 5,
            QuestionCategory.EXPERIENCE_GAP: 3 if seed.candidate_gaps else 1,
            QuestionCategory.CANDIDATE_QUESTIONS: 3,
        }

        # Role-specific adjustments
        if "AI_DATA" in strategy_type or "GENAI" in strategy_type:
            quotas[QuestionCategory.JD_TECHNICAL] += 2
            quotas[QuestionCategory.PROJECT_DEEP_DIVE] += 1
        elif "GCP" in strategy_type:
            quotas[QuestionCategory.JD_TECHNICAL] += 2
            quotas[QuestionCategory.SCENARIO_BASED] += 1

        logger.info("Planned interview question quotas across %d categories (Total: ~%d questions)", len(quotas), sum(quotas.values()))
        return quotas
