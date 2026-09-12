import uuid
from typing import List, Dict, Any
from careerpilot.models.interview import SystemDesignScenario
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class SystemDesignEngine:
    """
    Generates role-specific, grounded System Design interview challenges
    complete with functional/non-functional requirements, scale assumptions,
    architecture diagrams in text, trade-offs, and likely follow-up questions.
    """

    @classmethod
    def generate_system_design_scenarios(
        cls,
        analysis: JobAnalysisResult,
        resume: TailoredResume,
    ) -> List[SystemDesignScenario]:
        scenarios: List[SystemDesignScenario] = []
        strat = resume.strategy.strategy_type.value

        # Scenario 1: Event-Driven Ingestion & ELT Pipeline (Data Engineering & GCP Foundation)
        sc1_id = f"sys_{uuid.uuid4().hex[:8]}"
        sc1 = SystemDesignScenario(
            scenario_id=sc1_id,
            title="Design a Scalable Event-Driven Batch & Stream Ingestion Pipeline on GCP",
            target_role=resume.strategy.target_role,
            functional_requirements=[
                "Ingest incoming transaction JSON/CSV files landing in Google Cloud Storage (GCS).",
                "Trigger automated schema validation and duplicate record elimination.",
                "Load verified records into Google BigQuery analytical storage with minimal latency.",
                "Execute hourly aggregations and post-load data quality reconciliation.",
            ],
            non_functional_requirements=[
                "High reliability: 99.95% pipeline uptime SLA.",
                "Sub-2-minute ingestion latency from GCS landing to BigQuery availability.",
                "Strict idempotency across pipeline retries and reprocessing.",
                "Cost optimization: Zero idle compute cost when no files are landing.",
            ],
            scale_assumptions=[
                "[Assumed Volume] ~500,000 daily transaction events (approx 5-15 MB/sec peak traffic).",
                "[Assumed Retention] 3 years historical analytical data stored in BigQuery (~2-5 TB total).",
                "[Assumed Schema] 25 columns per record with occasional upstream schema evolution.",
            ],
            architecture_components=[
                "Storage Landing: Google Cloud Storage (GCS) raw bronze bucket.",
                "Event Notification: GCS Object Finalize triggers publishing to Cloud Pub/Sub topic.",
                "Serverless Compute: Google Cloud Functions (Python) subscriber for parsing and initial validation.",
                "Analytical Warehouse: Google BigQuery (Partitioned by ingestion date, Clustered by customer_id & status).",
                "Orchestrator: Apache Airflow / Cloud Composer for scheduled hourly downstream DAGs.",
                "Alerting: Cloud Monitoring + Slack/Email webhooks for SLA threshold breaches.",
            ],
            data_flow=[
                "1. Source application writes file `transactions_YYYYMMDD_HHMM.json` into GCS landing bucket.",
                "2. GCS automatically fires an Object Notification to Pub/Sub topic `gcs-file-events`.",
                "3. Cloud Function consumes Pub/Sub message, validates payload format, schema datatypes, and generates idempotency hash.",
                "4. Clean records are loaded via BigQuery Storage Write API into staging table `raw_staging`.",
                "5. Hourly Airflow DAG executes MERGE statement into production table `fct_transactions`, updating existing IDs and inserting new records.",
                "6. Airflow executes post-load row count and null reconciliation checks.",
            ],
            storage="GCS raw archive (Bronze) -> BigQuery Staging (Silver) -> BigQuery Clustered Tables (Gold).",
            processing="Python (Cloud Functions) for lightweight parsing; BigQuery SQL engine for heavy ELT transformations.",
            orchestration="Apache Airflow DAG with task retries (exponential backoff) and SLA failure callbacks.",
            monitoring="BigQuery Information Schema for scan metrics; Cloud Monitoring for function execution errors.",
            failure_handling="Dead-Letter Queue (DLQ) in Pub/Sub for unparseable records; automated retry with backoff in Airflow.",
            security="IAM service accounts with least privilege; CMEK encryption for GCS and BigQuery.",
            cost_considerations="Partition pruning and clustering in BigQuery queries reduce byte scans by ~25%; serverless compute scales to zero.",
            trade_offs=[
                "Cloud Functions vs Dataflow: Chose Cloud Functions for cost efficiency and simplicity given 500k volume; Dataflow would be preferred at >50M records/day.",
                "Micro-batch vs True Streaming: Hourly BigQuery MERGE minimizes table partition write quota limits while meeting the 2-minute latency requirement.",
            ],
            follow_up_questions=[
                "How would you handle sudden 10x traffic spikes during Black Friday without hitting BigQuery rate limits?",
                "What strategies prevent duplicate records when Pub/Sub delivers at-least-once duplicate messages?",
                "How would you design zero-downtime schema evolution when upstream adds a new required field?",
            ],
        )
        scenarios.append(sc1)

        # Scenario 2: Hybrid RAG & AI Agent System (GenAI & AI Data Engineer Focus)
        if "AI_DATA" in strat or "GENAI" in strat:
            sc2_id = f"sys_{uuid.uuid4().hex[:8]}"
            sc2 = SystemDesignScenario(
                scenario_id=sc2_id,
                title="Design an Enterprise Hybrid RAG Platform with Dense-Sparse Search and Grounding Guardrails",
                target_role="AI Data Engineer / GenAI Engineer",
                functional_requirements=[
                    "Ingest diverse enterprise technical documents (PDF, Markdown, HTML).",
                    "Perform hybrid document indexing combining dense semantic vectors and sparse lexical search.",
                    "Retrieve top relevant chunks and fuse ranks using Reciprocal Rank Fusion (RRF).",
                    "Generate strictly grounded answers with citations using Google Gemini / Vertex AI.",
                    "Filter out hallucinated claims before returning output to users.",
                ],
                non_functional_requirements=[
                    "Retrieval Latency: P95 < 250ms for hybrid search and reranking.",
                    "Strict Grounding: Zero ungrounded factual hallucinations allowed.",
                    "Scalability: Support 50,000+ indexed documentation pages.",
                ],
                scale_assumptions=[
                    "[Assumed Corpus] 50,000 documents; average 500 words per chunk; ~200,000 total vector embeddings.",
                    "[Assumed Query QPS] 10 queries/sec during peak hours.",
                ],
                architecture_components=[
                    "Document Processing: Recursive character chunking (500 tokens, 50 token overlap).",
                    "Dense Index: FAISS / ChromaDB with `all-MiniLM-L6-v2` or `text-embedding-004`.",
                    "Sparse Index: Okapi BM25 index for exact technical keyword matching.",
                    "Rank Fusion: Reciprocal Rank Fusion (RRF) algorithm combining dense and sparse rank lists.",
                    "LLM Generation: Google Gemini API / Vertex AI with temperature=0.0 and system grounding prompt.",
                    "Truth Guard: Output verification filter checking returned entities against retrieved chunk context.",
                ],
                data_flow=[
                    "1. Document Ingestion pipeline chunks text and stores metadata (source URL, section, timestamp).",
                    "2. Chunks are converted to dense embeddings and indexed in FAISS, while tokenized into BM25 index.",
                    "3. User submits query: Query is concurrently searched against FAISS (dense) and BM25 (sparse).",
                    "4. RRF algorithm scores chunks: `RRF_Score = 1/(60 + Rank_Dense) + 1/(60 + Rank_Sparse)`.",
                    "5. Top-5 fused chunks are injected into LLM prompt with strict grounding instructions.",
                    "6. Generated answer passes Truth Guard entity check before delivery to user.",
                ],
                storage="ChromaDB / FAISS on local NVMe / SSD for vectors; SQLite / PostgreSQL for document metadata.",
                processing="Python async workers for parallel dense and sparse retrieval; Gemini API for inference.",
                orchestration="LangGraph stateful workflow managing retrieval -> rerank -> generate -> truth check steps.",
                monitoring="Grounding faithfulness score, retrieval precision@k, and latency per pipeline stage.",
                failure_handling="Fallback to BM25 sparse search if vector index is temporarily unreachable; fallback response if grounding fails.",
                security="Role-based access control (RBAC) metadata filters ensuring users only retrieve permitted documents.",
                cost_considerations="Local embedding caching and semantic caching reduce repeated LLM inference costs.",
                trade_offs=[
                    "Dense + Sparse vs Dense Only: Hybrid search provides superior accuracy for exact technical tokens (e.g. error codes, parameter names) where pure semantic vectors drift.",
                    "RRF vs Cross-Encoder: RRF is compute-efficient ($O(1)$) compared to heavy cross-encoder rerankers, maintaining sub-200ms latency.",
                ],
                follow_up_questions=[
                    "How would you evaluate retrieval quality quantitatively across a golden evaluation dataset?",
                    "How do you handle multi-hop queries that require aggregating facts across two separate documents?",
                    "What happens when retrieved chunks contain contradictory information from different document versions?",
                ],
            )
            scenarios.append(sc2)

        return scenarios
