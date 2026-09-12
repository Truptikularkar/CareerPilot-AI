import re
from typing import Dict, List, Set, Tuple, Optional
from careerpilot.core.constants import MatchLevel, KeywordDensityRisk
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class KeywordTaxonomyMatcher:
    """
    Normalizes technical skills and classifies keyword matching across 3 tiers:
    EXACT_MATCH, SYNONYM_MATCH, and SEMANTIC_MATCH.
    Detects keyword density and keyword stuffing risks.
    """

    # Canonical taxonomy map (canonical_name -> set of normalized aliases)
    CANONICAL_SYNONYMS: Dict[str, Set[str]] = {
        "PYTHON": {"python", "py", "python3", "python 3"},
        "SQL": {"sql", "structured query language", "ansi sql", "postgresql", "mysql"},
        "BIGQUERY": {"bigquery", "google bigquery", "bq"},
        "GCP": {"gcp", "google cloud", "google cloud platform", "google cloud storage", "gcs"},
        "AIRFLOW": {"airflow", "apache airflow", "cloud composer"},
        "GENAI": {"genai", "generative ai", "generative artificial intelligence"},
        "LLM": {"llm", "llms", "large language model", "large language models"},
        "RAG": {"rag", "retrieval-augmented generation", "retrieval augmented generation", "hybrid retrieval"},
        "FAISS": {"faiss", "facebook ai similarity search", "vector database", "vector search"},
        "BM25": {"bm25", "sparse retrieval", "sparse search", "okapi bm25"},
        "VERTEX_AI": {"vertex ai", "google vertex ai", "vertex"},
        "GEMINI": {"gemini", "google gemini", "gemini api", "gemini 1.5 flash"},
        "AI_AGENTS": {"ai agents", "ai agent", "autonomous agents", "agentic workflows", "agentic"},
        "DATA_QUALITY": {"data quality", "data validation", "anomaly detection", "schema validation"},
        "ETL": {"etl", "elt", "data pipeline", "data pipelines", "batch pipeline"},
        "AWS": {"aws", "amazon web services"},
        "REDSHIFT": {"redshift", "amazon redshift"},
        "S3": {"s3", "amazon s3"},
        "KUBERNETES": {"kubernetes", "k8s"},
        "SPARK": {"spark", "pyspark", "apache spark"},
        "DOCKER": {"docker", "containerization"},
        "LANGCHAIN": {"langchain", "langgraph"},
    }

    # Semantic relationships (generic category concept <-> specific implementations)
    SEMANTIC_RELATIONSHIPS: Dict[str, Set[str]] = {
        "cloud data warehouse": {"bigquery", "redshift", "snowflake", "synapse"},
        "vector database": {"faiss", "chromadb", "pinecone", "milvus", "qdrant"},
        "cloud orchestration": {"airflow", "cloud composer", "step functions", "data factory"},
        "cloud storage": {"gcs", "google cloud storage", "s3", "blob storage"},
        "serverless compute": {"cloud functions", "cloud run", "aws lambda"},
        "event streaming": {"pub/sub", "cloud pub/sub", "kafka", "kinesis"},
        "data observability": {"data quality", "anomaly detection", "monitoring"},
    }


    @classmethod
    def normalize_term(cls, term: str) -> str:
        """Converts raw skill string to upper-snake canonical key if recognized."""
        t_clean = term.lower().strip()
        t_clean = re.sub(r"[^\w\s\-\/\+]", "", t_clean)
        for canon, aliases in cls.CANONICAL_SYNONYMS.items():
            if t_clean in aliases or any(a in t_clean for a in aliases):
                return canon
        return t_clean.upper().replace(" ", "_").replace("-", "_")

    @classmethod
    def match_term_in_text(cls, term: str, text: str) -> Tuple[MatchLevel, Optional[str]]:
        """
        Determines the highest match level for a JD term in the resume text:
        1. EXACT_MATCH
        2. SYNONYM_MATCH
        3. SEMANTIC_MATCH
        4. GAP
        """
        term_clean = term.lower().strip()
        text_lower = text.lower()

        # 1. Exact string/word match
        term_words = [w for w in re.findall(r"[a-zA-Z0-9\+\#]+", term_clean) if len(w) > 1]
        exact_pattern = r"\b" + re.escape(term_clean) + r"\b"
        if re.search(exact_pattern, text_lower):
            return MatchLevel.EXACT_MATCH, f"Exact match found for '{term}'"

        # 2. Synonym match via canonical mapping
        canonical = cls.normalize_term(term)
        if canonical in cls.CANONICAL_SYNONYMS:
            aliases = cls.CANONICAL_SYNONYMS[canonical]
            for alias in aliases:
                if re.search(r"\b" + re.escape(alias) + r"\b", text_lower):
                    return MatchLevel.SYNONYM_MATCH, f"Synonym match: '{term}' matched via alias '{alias}'"

        # 3. Semantic concept match (only for generic concept terms, NOT proprietary vendor tools)
        is_vendor_tech = any(v in term_clean for v in ["aws", "azure", "redshift", "snowflake", "glue", "emr", "s3", "databricks", "kubernetes", "spark", "tableau", "power bi"])
        if not is_vendor_tech:
            for concept, specifics in cls.SEMANTIC_RELATIONSHIPS.items():
                if concept in term_clean:
                    for spec in specifics:
                        if re.search(r"\b" + re.escape(spec) + r"\b", text_lower):
                            return MatchLevel.SEMANTIC_MATCH, f"Semantic alignment: '{term}' conceptually evidenced by '{spec}'"

        # 4. Token overlap fallback (only for non-vendor technical terms)
        if not is_vendor_tech and term_words:
            cand_tokens = [w for w in term_words if len(w) > 2 and w not in ("data", "engineer", "cloud", "platform", "pipeline", "pipelines", "architecture", "systems", "frameworks")]
            if cand_tokens and any(re.search(r"\b" + re.escape(w) + r"\b", text_lower) for w in cand_tokens):
                matched_w = next(w for w in cand_tokens if re.search(r"\b" + re.escape(w) + r"\b", text_lower))
                return MatchLevel.SYNONYM_MATCH, f"Keyword match via technical token '{matched_w}'"

        return MatchLevel.GAP, None


    @classmethod
    def evaluate_keyword_density(cls, term: str, text: str) -> Tuple[int, KeywordDensityRisk]:
        """Calculates keyword occurrence frequency and detects stuffing risk."""
        term_clean = term.lower().strip()
        text_lower = text.lower()

        count = len(re.findall(r"\b" + re.escape(term_clean) + r"\b", text_lower))

        if count == 0:
            return 0, KeywordDensityRisk.LOW_COVERAGE
        elif count > 6:
            return count, KeywordDensityRisk.POTENTIAL_STUFFING
        else:
            return count, KeywordDensityRisk.HEALTHY
