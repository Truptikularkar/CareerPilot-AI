import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger
from careerpilot.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from careerpilot.rag.vector_store import LocalVectorClient, LocalVectorCollection

logger = get_logger(__name__)




class InterviewStore:
    """
    Manages the ChromaDB collection for general Technical Interview Knowledge.
    Provides conceptual depth, implementation patterns, optimization techniques,
    and system design patterns across core data engineering and GenAI topics.
    Fully isolated from the Candidate Evidence collection.
    """

    COLLECTION_NAME = "interview_knowledge"

    # Curated technical knowledge modules with structured subtopics and categories
    CURATED_KNOWLEDGE_MODULES = [
        # 1. RAG & Hybrid Retrieval
        {
            "topic": "RAG",
            "subtopic": "Hybrid Retrieval & Reciprocal Rank Fusion",
            "difficulty": "Advanced",
            "category": "Implementation",
            "technology": "FAISS, BM25, RRF, Cross-Encoder",
            "source_file": "rag.md",
            "content": (
                "Hybrid retrieval combines dense semantic vector search (e.g., FAISS, ChromaDB using bi-encoders) "
                "with sparse exact keyword retrieval (e.g., BM25, TF-IDF). Dense search captures semantic meaning "
                "and paraphrasing but may miss rare keywords, alphanumeric codes, or technical IDs. Sparse search "
                "guarantees high keyword precision. Reciprocal Rank Fusion (RRF) scores each document d using "
                "RRF_Score(d) = sum(1 / (k + rank_i(d))), typically with constant k=60, blending both rank lists "
                "without requiring normalized score calibration. A cross-encoder reranker can be applied subsequently "
                "on the top-k fused results for maximum relevance precision."
            ),
        },
        {
            "topic": "RAG",
            "subtopic": "Chunking Strategies & Context Engineering",
            "difficulty": "Intermediate",
            "category": "Architecture",
            "technology": "LangChain, LlamaIndex, Python",
            "source_file": "rag.md",
            "content": (
                "Effective RAG ingestion requires chunking strategies aligned with document semantics rather than arbitrary "
                "character splitting. Markdown and document structural chunking preserves section headers, tables, and code "
                "blocks as atomic units. Parent-Document / Small-to-Big retrieval embeds small sentences (100-200 tokens) "
                "for precise vector matching, while passing the larger parent paragraph (500-1000 tokens) to the LLM for generation. "
                "Context window management should also implement document metadata tagging and citation tracing to prevent hallucinations."
            ),
        },
        {
            "topic": "RAG",
            "subtopic": "Hallucination Control & Grounding Guardrails",
            "difficulty": "Advanced",
            "category": "Troubleshooting",
            "technology": "LLMs, Guardrails, Evaluation",
            "source_file": "rag.md",
            "content": (
                "Hallucination mitigation in enterprise RAG pipelines relies on tripartite verification: "
                "1. Faithfulness: Every assertion in the generated answer must be entailed by retrieved context chunks. "
                "2. Context Relevance: Retrieved chunks must directly address the user's query intent. "
                "3. Answer Relevance: The final response must directly answer the prompt without evasive drift. "
                "Architectures enforce grounding by extracting citations, using structured Pydantic schemas, and rejecting "
                "unsupported assertions using deterministic fallback paths."
            ),
        },

        # 2. GCP & Cloud Data Architecture
        {
            "topic": "GCP",
            "subtopic": "BigQuery Partitioning & Clustering",
            "difficulty": "Intermediate",
            "category": "Optimization",
            "technology": "Google BigQuery, SQL",
            "source_file": "gcp.md",
            "content": (
                "Google BigQuery optimization hinges on partitioning and clustering. Partitioning divides large tables "
                "into segments based on timestamp (ingestion-time or date column) or integer range, drastically pruning "
                "bytes scanned and reducing query costs. Clustering sorts data within each partition based on up to 4 "
                "high-cardinality filter/join columns (e.g., customer_id, event_type). Queries filtering on clustered "
                "columns skip irrelevant blocks via metadata pruning, improving query speed and cutting compute costs."
            ),
        },
        {
            "topic": "GCP",
            "subtopic": "Event-Driven Real-time Ingestion",
            "difficulty": "Advanced",
            "category": "Architecture",
            "technology": "Cloud Storage, Pub/Sub, Cloud Functions, BigQuery",
            "source_file": "gcp.md",
            "content": (
                "An event-driven serverless ingestion architecture on GCP utilizes Cloud Storage object finalize notifications "
                "triggering Pub/Sub topics. Cloud Functions or Cloud Run subscribers consume Pub/Sub events, validate file "
                "payloads, perform schema sanity checks, and trigger streaming or micro-batch loads into BigQuery. "
                "This guarantees sub-minute data availability, auto-scales to hundreds of thousands of events daily, "
                "and maintains dead-letter queues (DLQ) for failed message replays."
            ),
        },

        # 3. Data Engineering & Data Quality
        {
            "topic": "Data Engineering",
            "subtopic": "Data Quality Validation & Observability",
            "difficulty": "Intermediate",
            "category": "Implementation",
            "technology": "SQL, Airflow, Great Expectations, BigQuery",
            "source_file": "data_engineering.md",
            "content": (
                "Modern data quality frameworks enforce multi-dimensional assertions across ETL pipelines: "
                "1. Completeness: Null value percentage checks and row-count reconciliation across source and target. "
                "2. Uniqueness: Primary key duplicate detection and surrogate key collision prevention. "
                "3. Consistency: Foreign key referential integrity and schema drift detection. "
                "4. Validity: Range checks, regex formatting, and IQR-based adaptive statistical thresholding for anomaly detection. "
                "Validation failures trigger automated quarantine tables, preventing corrupt downstream analytical reports."
            ),
        },
        {
            "topic": "Data Engineering",
            "subtopic": "ETL vs ELT & Dimensional Modeling",
            "difficulty": "Intermediate",
            "category": "Concept",
            "technology": "Data Warehousing, Kimball, dbt, SQL",
            "source_file": "data_engineering.md",
            "content": (
                "ETL extracts data, transforms it on an intermediary compute engine (e.g. Spark), and loads it into the target. "
                "ELT loads raw data directly into scalable cloud data warehouses (e.g. BigQuery, Snowflake) and performs "
                "transformations in-engine using SQL. In dimensional modeling (Kimball methodology), star schemas organize data "
                "into central Fact tables (containing numerical business metrics) connected to surrounding Dimension tables "
                "(containing descriptive context), optimizing analytical read query performance."
            ),
        },

        # 4. Apache Airflow
        {
            "topic": "Airflow",
            "subtopic": "Dynamic DAGs, Idempotency & Failure Remediation",
            "difficulty": "Advanced",
            "category": "Implementation",
            "technology": "Apache Airflow, Python, dag_run.conf",
            "source_file": "data_engineering.md",
            "content": (
                "Idempotency in Apache Airflow ensures that executing a DAG run or task instance multiple times with the same "
                "logical date produces the identical outcome without duplicate records or side effects (e.g. using atomic table "
                "partitions or MERGE / UPSERT statements). Dynamic DAG configuration via dag_run.conf allows parameterized runtime "
                "execution for on-demand validation workflows. Automated failure remediation utilizes Airflow on_failure_callback "
                "hooks to classify transient network/API timeouts versus hard schema breakages, triggering automated retries or alerts."
            ),
        },

        # 5. SQL & Advanced Query Optimization
        {
            "topic": "SQL",
            "subtopic": "Window Functions & CTE Performance Tuning",
            "difficulty": "Intermediate",
            "category": "Optimization",
            "technology": "SQL, BigQuery, PostgreSQL",
            "source_file": "sql.md",
            "content": (
                "Window functions compute values across rows related to the current query row without collapsing rows into a single "
                "group (unlike GROUP BY). Functions like ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), and LEAD() over PARTITION BY "
                "and ORDER BY clauses enable cumulative metrics, time-series shifts, and deduplication. Common Table Expressions (CTEs) "
                "improve readability and modularity; in modern query optimizers, non-recursive CTEs are inlined and predicate pushdown "
                "is applied to avoid unnecessary full table scans."
            ),
        },

        # 6. Python & Backend Concurrency
        {
            "topic": "Python",
            "subtopic": "OOP, Generators, Decorators & FastAPI Concurrency",
            "difficulty": "Intermediate",
            "category": "Implementation",
            "technology": "Python, FastAPI, Asyncio",
            "source_file": "python.md",
            "content": (
                "Python generators (using yield) enable memory-efficient lazy evaluation over massive data streams. Decorators wrap "
                "functions with cross-cutting concerns like logging, timing, and authentication. In high-concurrency microservices, "
                "FastAPI uses Python's asyncio event loop to handle non-blocking asynchronous I/O (database calls, LLM API requests) "
                "efficiently across worker threads, avoiding thread starvation under high concurrent request volume."
            ),
        },

        # 7. LangChain & LangGraph
        {
            "topic": "LangGraph",
            "subtopic": "Stateful Agent Graphs, Tool Calling & Cyclic Loops",
            "difficulty": "Advanced",
            "category": "Architecture",
            "technology": "LangGraph, LangChain, StateGraph",
            "source_file": "langgraph.md",
            "content": (
                "LangGraph extends LLM orchestration into cyclic stateful graphs using TypedDict/Pydantic schemas. Nodes represent "
                "discrete processing steps (planners, tool executors, evaluators), while edges and conditional routing determine "
                "execution flow. Checkpointing enables state persistence, error recovery, time-travel debugging, and human-in-the-loop "
                "intervention. This architecture prevents infinite loops through max-step bounds and enables autonomous self-correction."
            ),
        },

        # 8. Apache Spark & Distributed Computing
        {
            "topic": "Spark",
            "subtopic": "Spark Architecture, Shuffle Optimization & Broadcast Joins",
            "difficulty": "Advanced",
            "category": "Optimization",
            "technology": "Apache Spark, PySpark",
            "source_file": "spark.md",
            "content": (
                "Apache Spark coordinates distributed computation via Driver and Executor nodes over Resilient Distributed Datasets "
                "(RDDs) and DataFrames. Transformations are categorized into Narrow (e.g. map, filter — within same partition) and "
                "Wide (e.g. groupBy, join — requiring data shuffling across the network). Shuffle optimization involves eliminating data "
                "skew, adjusting spark.sql.shuffle.partitions, and leveraging Broadcast Hash Joins for joining large tables with small "
                "dimension tables (<10MB) to eliminate costly cross-node shuffles."
            ),
        },

        # 9. AWS & Cloud Comparison
        {
            "topic": "AWS",
            "subtopic": "AWS Data Architecture & GCP Equivalents",
            "difficulty": "Intermediate",
            "category": "Concept",
            "technology": "S3, Glue, Redshift, Lambda vs GCP",
            "source_file": "aws.md",
            "content": (
                "Core cloud data services map directly between major providers: "
                "Object Storage: Amazon S3 <=> Google Cloud Storage (GCS). "
                "Data Warehousing: Amazon Redshift <=> Google BigQuery. "
                "Serverless Compute: AWS Lambda <=> Google Cloud Functions. "
                "ETL & Metadata Catalog: AWS Glue / EMR <=> Google Dataproc / Dataflow / Dataplex. "
                "Event Streaming: Amazon Kinesis / EventBridge <=> Google Cloud Pub/Sub. "
                "Understanding these architectural parallels allows rapid transfer of pipeline engineering expertise between clouds."
            ),
        },
    ]

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        client: Optional[Any] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = client or LocalVectorClient(path=self.persist_directory)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.collection: LocalVectorCollection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> LocalVectorCollection:
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "Interview & Technical Knowledge Store for CareerPilot AI"},
        )


    def clear(self) -> None:
        """Deletes and recreates the interview knowledge collection."""
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            logger.info("Deleted collection '%s'", self.COLLECTION_NAME)
        except Exception as e:
            logger.debug("Collection deletion exception (normal if non-existent): %s", e)
        self.collection = self._get_or_create_collection()

    def parse_interview_directory(self, knowledge_dir: Path) -> List[Dict[str, Any]]:
        """
        Parses knowledge files in data/knowledge/interview/ and combines them
        with curated deep conceptual knowledge modules.
        """
        chunks: List[Dict[str, Any]] = []

        # 1. Ingest curated comprehensive technical modules
        for idx, mod in enumerate(self.CURATED_KNOWLEDGE_MODULES):
            topic_clean = mod["topic"].lower().replace(" ", "_")
            sub_clean = mod["subtopic"][:12].lower().replace(" ", "_")
            chunk_id = f"tech_{topic_clean}_{idx+1}_{sub_clean}"
            chunk_id = re.sub(r"[^a-zA-Z0-9_]", "", chunk_id)

            chunks.append({
                "chunk_id": chunk_id,
                "text": f"[{mod['topic']} - {mod['subtopic']}] ({mod['category']}): {mod['content']}",
                "metadata": {
                    "topic": mod["topic"],
                    "subtopic": mod["subtopic"],
                    "difficulty": mod["difficulty"],
                    "category": mod["category"],
                    "technology": mod["technology"],
                    "source_file": mod["source_file"],
                }
            })

        # 2. Ingest raw files from knowledge_dir if present
        if knowledge_dir.exists():
            for f in sorted(knowledge_dir.glob("*.md")):
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        content = file.read().strip()
                    if content:
                        topic_name = f.stem.replace("_", " ").title()
                        chunk_id = f"tech_seed_{f.stem}"
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": f"[Technical Seed: {topic_name}] {content}",
                            "metadata": {
                                "topic": topic_name,
                                "subtopic": "Seed Topics",
                                "difficulty": "Intermediate",
                                "category": "Concept",
                                "technology": topic_name,
                                "source_file": f.name,
                            }
                        })
                except Exception as e:
                    logger.error("Error reading knowledge file '%s': %s", f.name, e)

        logger.info("Parsed %d technical interview knowledge chunks.", len(chunks))
        return chunks

    def index_interview_data(self, knowledge_dir: Optional[Path] = None, clear_existing: bool = True) -> int:
        """
        Indexes all technical knowledge data into ChromaDB.
        Safe against duplicates via deterministic chunk IDs and upsert.
        """
        know_dir = knowledge_dir or Path("data/knowledge/interview")

        if clear_existing:
            self.clear()

        chunks = self.parse_interview_directory(know_dir)
        if not chunks:
            logger.warning("No technical chunks found to index.")
            return 0

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # Generate embeddings
        embeddings = self.embedding_provider.embed_documents(texts)

        # Upsert into collection (safe against duplicates)
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Successfully indexed %d technical chunks in '%s'.", len(ids), self.COLLECTION_NAME)
        return len(ids)

    def count(self) -> int:
        """Return total number of chunks indexed in interview store."""
        return self.collection.count()
