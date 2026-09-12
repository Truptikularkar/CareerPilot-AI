from typing import Optional, Union
from careerpilot.core.constants import ResumeStrategyType, RoleCategory
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import ResumeStrategy
from careerpilot.generators.strategy_engine import StrategyEngine
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class StrategySelector:
    """
    Selects the optimal resume tailoring strategy from a structured JobAnalysisResult
    or applies a user-selected strategy override.
    """

    @classmethod
    def select_strategy(
        cls,
        analysis: JobAnalysisResult,
        override_strategy: Optional[Union[str, ResumeStrategyType]] = None,
    ) -> ResumeStrategy:
        if override_strategy and override_strategy != ResumeStrategyType.AUTO:
            if isinstance(override_strategy, str):
                strat_type = ResumeStrategyType(override_strategy)
            else:
                strat_type = override_strategy
            reason = f"User explicitly selected manual override strategy: {strat_type.value}"
            logger.info(reason)
            return StrategyEngine.get_strategy(strat_type, reasoning=reason)

        primary_role = analysis.role_classification.primary_role
        work_dist = analysis.role_reality.work_distribution
        title_lower = analysis.job_title.lower()


        # Decision routing based on Job Analysis and Title
        if "genai" in title_lower or "rag" in title_lower or primary_role == RoleCategory.GENAI_ENGINEER:
            strat_type = ResumeStrategyType.GENAI_ENGINEER
            reason = f"Job Classified as GenAI / RAG Engineer focusing heavily on RAG, Agents, and LLM Applications ({work_dist.get('GenAI / RAG / Agents', 0)}%)."

        elif ("gcp" in title_lower and "data" in title_lower) or primary_role == RoleCategory.GCP_DATA_ENGINEER:
            strat_type = ResumeStrategyType.GCP_DATA_ENGINEER
            reason = "Job specifically mandates Google Cloud Platform (BigQuery, Pub/Sub, Cloud Storage) data infrastructure."
        elif primary_role == RoleCategory.AI_DATA_ENGINEER:
            strat_type = ResumeStrategyType.AI_DATA_ENGINEER
            reason = f"Job Classified as AI Data Engineer with strong dual emphasis on Data Pipelines ({work_dist.get('Data Engineering', 0)}%) and GenAI ({work_dist.get('GenAI / RAG / Agents', 0)}%)."
        elif primary_role in (RoleCategory.DATA_ENGINEER, RoleCategory.CLOUD_DATA_ENGINEER, RoleCategory.ANALYTICS_ENGINEER):
            strat_type = ResumeStrategyType.DATA_ENGINEER
            reason = f"Job Classified as Data Engineer focusing on ETL, SQL, BigQuery, and pipeline orchestration ({work_dist.get('Data Engineering', 0)}%)."
        else:
            # Fallback to candidate's top priority career direction
            strat_type = ResumeStrategyType.AI_DATA_ENGINEER
            reason = "Defaulting to AI Data Engineer strategy for optimal cross-functional alignment."


        logger.info("Selected Resume Strategy: %s (Reason: %s)", strat_type.value, reason)
        return StrategyEngine.get_strategy(strat_type, reasoning=reason)
