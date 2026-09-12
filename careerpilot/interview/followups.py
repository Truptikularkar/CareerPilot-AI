from typing import List, Dict, Any
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class FollowUpEngine:
    """
    Generates realistic 4-tier interviewer follow-up chains:
    Primary -> Follow-up 1 -> Follow-up 2 -> Challenge -> Why?
    """

    DEFAULT_FOLLOWUPS: Dict[str, List[str]] = {
        "bigquery": [
            "What is the underlying physical difference between partitioning and clustering in BigQuery storage?",
            "How do partition filters reduce byte scans and query processing costs?",
            "When would table clustering lead to sub-optimal performance compared to partitioning?",
            "Why did you choose daily ingestion partitioning over ingestion-time clustering?",
        ],
        "airflow": [
            "How do you design Airflow DAGs to be strictly idempotent across historical backfills?",
            "What mechanisms did you implement to handle transient worker failures and retries?",
            "How did your GenAI root-cause agent extract error logs from failed Airflow task instances?",
            "Why use Airflow instead of native GCP Cloud Composer or Eventarc triggers?",
        ],
        "rag": [
            "Why combine dense semantic embeddings (FAISS) with sparse BM25 keyword search?",
            "How does Reciprocal Rank Fusion (RRF) balance relevance scores from heterogeneous retrievers?",
            "How did you prevent LLM hallucination and ensure strict grounding against retrieved chunks?",
            "Why build a local offline RAG sandbox instead of using managed cloud vector search?",
        ],
        "data_quality": [
            "What specific data validation checks did you run before loading into reporting marts?",
            "How did you utilize BigQuery ML for automated statistical anomaly detection?",
            "How do you handle schema drift when upstream source systems alter column data types?",
            "Why decouple data validation into post-ingestion DAG steps rather than inline streaming checks?",
        ],
        "pubsub": [
            "How did you guarantee at-least-once message processing and eliminate duplicate records?",
            "What happens if Cloud Functions execution times out during high-volume spikes?",
            "How would this architecture change if daily ingestion volume increased from 500k to 50M records?",
            "Why choose Pub/Sub over Apache Kafka for this event-driven ingestion workflow?",
        ],
    }

    @classmethod
    def generate_followup_chain(cls, topic_or_question: str) -> List[str]:
        topic_lower = topic_or_question.lower()
        for key, chain in cls.DEFAULT_FOLLOWUPS.items():
            if key in topic_lower:
                return chain

        # Generic technical follow-up chain
        return [
            "Can you walk through the step-by-step internal execution flow of that component?",
            "What happens when an unexpected exception or corrupted record enters this stage?",
            "What trade-offs did you evaluate between latency, compute cost, and operational complexity?",
            "Why was this particular architectural approach chosen over alternative solutions?",
        ]
