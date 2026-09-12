from typing import List, Dict, Any, Optional
from careerpilot.models.ats import RequirementCoverageItem, InterviewReadinessSeed
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class InterviewReadinessSeedGenerator:
    """
    Generates structured Interview Readiness signals bridging the tailored resume
    and Job Description to prepare the seed contract for Milestone 6 Interview Engine.
    """

    @classmethod
    def generate_seed(
        cls,
        analysis: JobAnalysisResult,
        resume: TailoredResume,
        coverage_matrix: List[RequirementCoverageItem],
    ) -> InterviewReadinessSeed:
        # High priority skills (overlapping in both JD and candidate verified history)
        high_priority = [m.requirement for m in coverage_matrix if m.match_level.value != "GAP"]
        gaps = [m.requirement for m in coverage_matrix if m.match_level.value == "GAP"]

        # Likely interview topics based on target role
        strat = resume.strategy.strategy_type.value
        if "AI_DATA_ENGINEER" in strat or "GENAI" in strat:
            likely_topics = [
                "BigQuery query cost optimization via partitioning & clustering",
                "Apache Airflow DAG design, retries, and SLA alerting",
                "Hybrid Retrieval mechanics (FAISS dense + BM25 sparse + Reciprocal Rank Fusion)",
                "AI Agentic failure triage using Gemini and Vertex AI",
                "Data Quality validation and automated statistical anomaly detection",
            ]
            scenarios = [
                "Diagnosing and recovering from a critical Airflow batch pipeline failure",
                "Mitigating LLM hallucination in enterprise documentation Q&A via grounding guardrails",
                "Handling sudden schema drift and corrupt transaction records in BigQuery ingestion",
            ]
            system_designs = [
                "Event-driven serverless ingestion on GCP (Cloud Storage -> Pub/Sub -> Cloud Functions -> BigQuery)",
                "Enterprise RAG architecture with dense/sparse hybrid search and metadata filtering",
            ]
        else:
            likely_topics = [
                "BigQuery SQL optimization, table clustering, and partition maintenance",
                "Modular Apache Airflow DAG engineering and dependency management",
                "Automated data quality rule frameworks and row-count reconciliation",
                "Transferable cloud data patterns between GCP and AWS",
            ]
            scenarios = [
                "Optimizing slow analytical queries on 500k+ daily transaction tables",
                "Implementing idempotency and backfill strategies for historical data pipelines",
            ]
            system_designs = [
                "Scalable batch ETL/ELT pipeline with automated data quality gates",
            ]

        # Key candidate verified strengths & metric claims likely to be challenged
        challenged_claims = [
            "Verified ~25% BigQuery cost reduction: Be ready to explain partition filters vs clustering keys.",
            "Verified ~75% Airflow transient error resolution: Be ready to explain LLM log parsing and auto-retry triggers.",
            "Verified ~35% data quality incident reduction: Be ready to explain automated validation checks.",
            "Verified 1.9+ years professional experience: Frame depth of production delivery over chronological tenure.",
        ]

        behavioral_themes = [
            "Cross-functional collaboration with data science and analytics engineering teams",
            "Root-cause problem solving during on-call production incidents",
            "Continuous learning and fast adaptation to new cloud and GenAI technologies",
        ]

        seed = InterviewReadinessSeed(
            job_id=analysis.job_id,
            target_role=resume.strategy.target_role,
            high_priority_skills=high_priority[:8],
            candidate_strengths=analysis.key_strengths[:8],
            candidate_gaps=gaps[:6],
            likely_interview_topics=likely_topics,
            risky_requirements=analysis.key_gaps[:5],
            challenged_claims=challenged_claims,
            scenario_topics=scenarios,
            system_design_topics=system_designs,
            behavioral_themes=behavioral_themes,
        )

        logger.info("Generated InterviewReadinessSeed for Job '%s' (Role: %s)", analysis.job_id, seed.target_role)
        return seed
