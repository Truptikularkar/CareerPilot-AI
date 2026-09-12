from typing import Dict, List, Any
from careerpilot.core.constants import ResumeStrategyType, RoleCategory
from careerpilot.models.resume import ResumeStrategy
from careerpilot.models.job import JobAnalysisResult
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class StrategyEngine:
    """
    Defines targeted resume tailoring configurations for the candidate's verified background.
    Preserves single verified truth while tuning emphasis, project prioritization, and skills layout.
    """

    STRATEGY_CONFIGS: Dict[ResumeStrategyType, Dict[str, Any]] = {
        ResumeStrategyType.AI_DATA_ENGINEER: {
            "target_role": "AI Data Engineer",
            "summary_tone": "AI & Data Platform Engineering",
            "emphasis_keywords": [
                "Python", "SQL", "Google Cloud Platform (GCP)", "BigQuery", "Apache Airflow",
                "RAG", "Vertex AI", "Gemini API", "AI Agents", "Data Quality", "ETL/ELT",
            ],
            "project_priorities": [
                "AI-Driven Data Quality Monitoring",
                "AI AutoHeal Agent",
                "Local RAG & Hybrid Retrieval",
            ],
            "skill_priorities": [
                "Data Engineering & Cloud", "AI / GenAI & LLMs", "Programming & Databases", "Orchestration & DevOps",
            ],
            "summary_template": (
                "AI Data Engineer with 1.9+ years of professional experience building automated ETL/ELT pipelines, "
                "enterprise data validation frameworks, and grounded generative AI workflows on Google Cloud Platform. "
                "Demonstrated expertise in Python, SQL, BigQuery cost optimization (~25%), Apache Airflow, and RAG/Agentic "
                "monitoring systems resolving 75% of transient data pipeline failures automatically."
            ),
        },
        ResumeStrategyType.DATA_ENGINEER: {
            "target_role": "Data Engineer",
            "summary_tone": "Data Pipeline & Warehouse Engineering",
            "emphasis_keywords": [
                "Python", "SQL", "BigQuery", "Apache Airflow", "ETL / ELT",
                "Google Cloud Platform (GCP)", "Data Quality", "Partitioning & Clustering",
                "Cloud Storage", "Pub/Sub", "Data Validation",
            ],
            "project_priorities": [
                "AI-Driven Data Quality Monitoring",
                "Automated Sales Data Validation DAG",
                "AI AutoHeal Agent",
            ],
            "skill_priorities": [
                "Data Engineering & Pipelines", "Databases & Cloud Warehouses", "Programming & SQL", "Cloud & Orchestration",
            ],
            "summary_template": (
                "Data Engineer with 1.9+ years of experience designing, automating, and scaling robust ETL/ELT data pipelines "
                "and analytical data warehouses in Google BigQuery. Proven track record reducing query costs by ~25% through "
                "partitioning/clustering, authoring modular Apache Airflow DAGs, and engineering automated data validation "
                "rules reducing data quality incidents by 35%."
            ),
        },
        ResumeStrategyType.GENAI_ENGINEER: {
            "target_role": "Generative AI / RAG Engineer",
            "summary_tone": "LLM Orchestration & Grounded Retrieval",
            "emphasis_keywords": [
                "Generative AI", "RAG", "Hybrid Retrieval", "FAISS", "BM25",
                "Reciprocal Rank Fusion", "Vertex AI", "Gemini API", "AI Agents",
                "Python", "SQL", "Grounding Guardrails",
            ],
            "project_priorities": [
                "Local RAG & Hybrid Retrieval",
                "AI AutoHeal Agent",
                "AI-Driven Data Quality Monitoring",
            ],
            "skill_priorities": [
                "Generative AI & LLM Systems", "Retrieval & Vector Search", "Programming & Backend", "Cloud Infrastructure",
            ],
            "summary_template": (
                "Generative AI & LLM Engineer with 1.9+ years of engineering experience developing grounded RAG architectures, "
                "multi-agent orchestration graphs, and intelligent pipeline monitoring solutions. Deep hands-on expertise "
                "implementing dense and sparse hybrid retrieval (FAISS + BM25 + RRF), Vertex AI/Gemini integration, and automated "
                "root-cause analysis agents."
            ),
        },
        ResumeStrategyType.GCP_DATA_ENGINEER: {
            "target_role": "GCP Cloud Data Engineer",
            "summary_tone": "Google Cloud Platform Data Architecture",
            "emphasis_keywords": [
                "Google Cloud Platform (GCP)", "BigQuery", "Cloud Storage", "Pub/Sub",
                "Cloud Functions", "Cloud Run", "Apache Airflow", "Python", "SQL",
                "Cost Optimization", "Event-Driven Ingestion",
            ],
            "project_priorities": [
                "AI AutoHeal Agent",
                "AI-Driven Data Quality Monitoring",
                "Automated Sales Data Validation DAG",
            ],
            "skill_priorities": [
                "GCP Cloud Architecture", "Data Warehouse & BigQuery", "Pipeline Orchestration", "Programming & Automation",
            ],
            "summary_template": (
                "GCP Cloud Data Engineer with 1.9+ years of professional production experience architecting serverless, "
                "event-driven data pipelines on Google Cloud Platform. Specialized in high-performance BigQuery optimization, "
                "Pub/Sub real-time ingestion, Cloud Functions automation, and Airflow orchestration for mission-critical enterprise workflows."
            ),
        },
    }

    @classmethod
    def get_strategy(cls, strategy_type: ResumeStrategyType, reasoning: str = "") -> ResumeStrategy:
        """Retrieves structured strategy configuration."""
        if strategy_type == ResumeStrategyType.AUTO or strategy_type not in cls.STRATEGY_CONFIGS:
            strategy_type = ResumeStrategyType.AI_DATA_ENGINEER

        cfg = cls.STRATEGY_CONFIGS[strategy_type]
        return ResumeStrategy(
            strategy_type=strategy_type,
            target_role=cfg["target_role"],
            emphasis_keywords=cfg["emphasis_keywords"],
            summary_tone=cfg["summary_tone"],
            project_priorities=cfg["project_priorities"],
            skill_priorities=cfg["skill_priorities"],
            reasoning=reasoning or f"Tailored strategy for {cfg['target_role']} profile.",
        )
