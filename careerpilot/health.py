from typing import Dict, Any, List, Optional
from pathlib import Path
from careerpilot.core.constants import HealthStatus, AppEnvironmentMode
from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger

logger = get_logger("careerpilot.health")


class ComponentHealth:
    def __init__(self, name: str, status: HealthStatus, message: str, details: Optional[Dict[str, Any]] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
        }


class HealthReport:
    def __init__(self, overall_status: HealthStatus, components: List[ComponentHealth]):
        self.overall_status = overall_status
        self.components = components

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "components": [c.to_dict() for c in self.components],
        }


def check_configuration() -> ComponentHealth:
    """Verifies core application settings and environment mode."""
    details = {
        "mode": settings.CAREERPILOT_MODE.value,
        "llm_provider": settings.LLM_PROVIDER.value,
        "is_demo_mode": settings.is_demo_mode,
        "masked_api_key": settings.masked_gemini_key if settings.GEMINI_API_KEY else "Not Configured",
    }
    return ComponentHealth("Configuration", HealthStatus.HEALTHY, f"Running in {settings.CAREERPILOT_MODE.value} mode.", details)


def check_candidate_data() -> ComponentHealth:
    """Verifies candidate ground truth files in active candidate directory."""
    cand_dir = settings.active_candidate_dir
    required_files = ["profile.yaml", "experience.md", "projects.md", "skills.md", "achievements.md", "preferences.yaml"]
    missing = [f for f in required_files if not (cand_dir / f).exists()]

    if not cand_dir.exists():
        return ComponentHealth("Candidate Data", HealthStatus.UNAVAILABLE, f"Active candidate directory '{cand_dir}' does not exist.", {"missing": required_files})

    if missing:
        return ComponentHealth("Candidate Data", HealthStatus.DEGRADED, f"Missing files in {cand_dir.name}: {missing}", {"missing": missing})

    return ComponentHealth("Candidate Data", HealthStatus.HEALTHY, f"All {len(required_files)} candidate source files verified in '{cand_dir.name}/'.", {"directory": str(cand_dir.name)})


def check_knowledge_data() -> ComponentHealth:
    """Verifies technical interview knowledge base files."""
    k_dir = settings.KNOWLEDGE_DATA_DIR
    if not k_dir.exists():
        return ComponentHealth("Knowledge Base", HealthStatus.DEGRADED, "Knowledge directory missing.", {})

    k_files = list(k_dir.rglob("*.md"))
    if not k_files:
        return ComponentHealth("Knowledge Base", HealthStatus.DEGRADED, "No markdown knowledge files found in data/knowledge/.", {})

    return ComponentHealth("Knowledge Base", HealthStatus.HEALTHY, f"Found {len(k_files)} technical interview knowledge topics.", {"files_count": len(k_files)})


def check_database() -> ComponentHealth:
    """Verifies database connectivity across SQLite and PostgreSQL."""
    try:
        from careerpilot.db.session import engine, init_db
        init_db()
        from sqlalchemy import text
        with engine.connect() as conn:
            if engine.dialect.name == "sqlite":
                res = conn.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table'")).scalar()
            else:
                res = conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")).scalar()
        db_type = "PostgreSQL" if engine.dialect.name == "postgresql" else "SQLite"
        return ComponentHealth("Database", HealthStatus.HEALTHY, f"{db_type} database connected with {res} tables.", {"tables_count": res})
    except Exception as e:
        logger.error("Health check database failure: %s", str(e))
        return ComponentHealth("Database", HealthStatus.UNAVAILABLE, f"Database connectivity error: {str(e)}", {})


def check_embedding_model() -> ComponentHealth:
    """Verifies local embedding provider."""
    try:
        from careerpilot.rag.embeddings import get_embedding_provider
        provider = get_embedding_provider()
        dim = provider.dimension
        return ComponentHealth("Embedding Model", HealthStatus.HEALTHY, f"Embedding model '{settings.EMBEDDING_MODEL_NAME}' operational (Dim: {dim}).", {"dimension": dim})
    except Exception as e:
        logger.error("Health check embedding failure: %s", str(e))
        return ComponentHealth("Embedding Model", HealthStatus.DEGRADED, f"Embedding model fallback: {str(e)}", {})


def check_vector_store() -> ComponentHealth:
    """Verifies ChromaDB vector stores."""
    try:
        from careerpilot.rag.indexer import initialize_vector_store
        cand_coll, know_coll = initialize_vector_store()
        cand_count = cand_coll.count()
        know_count = know_coll.count()
        return ComponentHealth(
            "Vector Store",
            HealthStatus.HEALTHY,
            f"ChromaDB ready: {cand_count} candidate chunks, {know_count} knowledge chunks.",
            {"candidate_chunks": cand_count, "knowledge_chunks": know_count}
        )
    except Exception as e:
        logger.error("Health check vector store failure: %s", str(e))
        return ComponentHealth("Vector Store", HealthStatus.DEGRADED, f"Vector store warning: {str(e)}", {})


def check_llm_provider() -> ComponentHealth:
    """Verifies LLM configuration."""
    from careerpilot.llm.factory import get_llm_provider
    provider = get_llm_provider()
    if settings.LLM_PROVIDER.value == "gemini" and not settings.GEMINI_API_KEY:
        return ComponentHealth(
            "LLM Provider",
            HealthStatus.DEGRADED,
            "GEMINI_API_KEY not configured. Falling back to deterministic offline rules & Mock LLM.",
            {"provider": provider.provider_name}
        )
    return ComponentHealth(
        "LLM Provider",
        HealthStatus.HEALTHY,
        f"Configured LLM provider: {provider.provider_name}.",
        {"provider": provider.provider_name}
    )


def get_system_health() -> HealthReport:
    """Runs all component health checks and determines overall system status."""
    components = [
        check_configuration(),
        check_candidate_data(),
        check_knowledge_data(),
        check_database(),
        check_embedding_model(),
        check_vector_store(),
        check_llm_provider(),
    ]

    statuses = [c.status for c in components]
    if HealthStatus.UNAVAILABLE in statuses:
        overall = HealthStatus.UNAVAILABLE
    elif HealthStatus.DEGRADED in statuses:
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY

    return HealthReport(overall, components)
