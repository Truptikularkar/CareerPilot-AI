from pathlib import Path
from typing import Tuple, Dict, Any
from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.rag.interview_store import InterviewStore
from careerpilot.rag.embeddings import get_embedding_provider

logger = get_logger("careerpilot.rag.indexer")


def initialize_vector_store() -> Tuple[Any, Any]:
    """
    Initializes and returns the candidate evidence and technical knowledge collections.
    Ensures vector store is ready on startup.
    """
    cand_store = CandidateStore()
    interview_store = InterviewStore()
    return cand_store.collection, interview_store.collection


def build_or_load_indexes(force_reindex: bool = False) -> Dict[str, Any]:
    """
    Checks if vector stores exist and are populated.
    If empty or force_reindex is True, indexes candidate data and knowledge base.
    """
    cand_dir = settings.active_candidate_dir
    know_dir = settings.KNOWLEDGE_DATA_DIR / "interview" if (settings.KNOWLEDGE_DATA_DIR / "interview").exists() else settings.KNOWLEDGE_DATA_DIR

    cand_store = CandidateStore()
    interview_store = InterviewStore()

    cand_count = cand_store.collection.count()
    know_count = interview_store.collection.count()

    if force_reindex or cand_count == 0:
        logger.info("Indexing candidate evidence from canonical database...")
        try:
            from careerpilot.services.candidate_service import CandidateService
            cand_count = CandidateService.rebuild_candidate_rag()
        except Exception as e:
            logger.warning("Could not build candidate RAG from database, falling back to %s: %s", cand_dir, e)
            cand_count = cand_store.index_candidate_data(candidate_dir=cand_dir, clear_existing=True)

    if force_reindex or know_count == 0:
        logger.info("Indexing technical interview knowledge from %s...", know_dir)
        know_count = interview_store.index_interview_data(knowledge_dir=know_dir, clear_existing=True)

    return {
        "candidate_chunks": cand_count,
        "knowledge_chunks": know_count,
        "status": "READY",
    }
