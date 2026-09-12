from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from careerpilot.core.logging import get_logger
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.rag.interview_store import InterviewStore
from careerpilot.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider

logger = get_logger(__name__)


class RetrievalResult(BaseModel):
    """Structured result returned by the DualStoreRetriever for truth audit and LLM consumption."""
    text: str
    chunk_id: str
    source: str
    evidence_status: str = "SUPPORTED"
    evidence_type: str = "professional"
    skills: str = ""
    technologies: str = ""
    verified: bool = True
    allowed_for_resume: bool = True
    allowed_for_interview: bool = True
    distance: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DualStoreRetriever:
    """
    Unified retriever providing source-aware, metadata-filtered semantic search
    across isolated Candidate Evidence and Interview Knowledge stores.
    """

    def __init__(
        self,
        candidate_store: Optional[CandidateStore] = None,
        interview_store: Optional[InterviewStore] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.candidate_store = candidate_store or CandidateStore(embedding_provider=self.embedding_provider)
        self.interview_store = interview_store or InterviewStore(embedding_provider=self.embedding_provider)

    def retrieve_candidate_evidence(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        evidence_status: Optional[str] = "SUPPORTED",
        allowed_for_resume_only: bool = False,
    ) -> List[RetrievalResult]:
        """
        Retrieves verified candidate facts/experience matching the query.
        Applies truth guardrails (e.g. only returning SUPPORTED evidence by default).
        """
        query_embedding = self.embedding_provider.embed_text(query)

        # Build ChromaDB where filter
        where_clauses = []
        if filters:
            for k, v in filters.items():
                where_clauses.append({k: v})

        if evidence_status:
            where_clauses.append({"evidence_status": evidence_status})

        if allowed_for_resume_only:
            where_clauses.append({"allowed_for_resume": True})

        where_filter = None
        if len(where_clauses) == 1:
            where_filter = where_clauses[0]
        elif len(where_clauses) > 1:
            where_filter = {"$and": where_clauses}

        results = self.candidate_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        retrieval_items: List[RetrievalResult] = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            ids = results["ids"][0] if results["ids"] else [""] * len(docs)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)

            for doc, meta, chunk_id, dist in zip(docs, metas, ids, distances):
                retrieval_items.append(
                    RetrievalResult(
                        text=doc,
                        chunk_id=chunk_id,
                        source=meta.get("source_file", "unknown"),
                        evidence_status=meta.get("evidence_status", "SUPPORTED"),
                        evidence_type=meta.get("evidence_type", "professional"),
                        skills=meta.get("skills", ""),
                        technologies=meta.get("technologies", ""),
                        verified=meta.get("verified", True),
                        allowed_for_resume=meta.get("allowed_for_resume", True),
                        allowed_for_interview=meta.get("allowed_for_interview", True),
                        distance=float(dist),
                        metadata=meta,
                    )
                )

        logger.info(
            "Retrieved %d candidate evidence chunks for query: '%s' (filter: %s)",
            len(retrieval_items),
            query[:40],
            where_filter,
        )
        return retrieval_items

    def retrieve_interview_knowledge(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        topic: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieves general technical interview concepts, algorithms, and system design patterns.
        """
        query_embedding = self.embedding_provider.embed_text(query)

        where_clauses = []
        if filters:
            for k, v in filters.items():
                where_clauses.append({k: v})

        if topic:
            where_clauses.append({"topic": topic})

        where_filter = None
        if len(where_clauses) == 1:
            where_filter = where_clauses[0]
        elif len(where_clauses) > 1:
            where_filter = {"$and": where_clauses}

        results = self.interview_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        retrieval_items: List[RetrievalResult] = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            ids = results["ids"][0] if results["ids"] else [""] * len(docs)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)

            for doc, meta, chunk_id, dist in zip(docs, metas, ids, distances):
                retrieval_items.append(
                    RetrievalResult(
                        text=doc,
                        chunk_id=chunk_id,
                        source=meta.get("source_file", "knowledge"),
                        evidence_status="SUPPORTED",
                        evidence_type="interview_knowledge",
                        skills=meta.get("technology", meta.get("topic", "")),
                        technologies=meta.get("technology", ""),
                        verified=True,
                        allowed_for_resume=False,
                        allowed_for_interview=True,
                        distance=float(dist),
                        metadata=meta,
                    )
                )

        logger.info(
            "Retrieved %d technical knowledge chunks for query: '%s'",
            len(retrieval_items),
            query[:40],
        )
        return retrieval_items


_default_retriever = None


def get_retriever() -> DualStoreRetriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = DualStoreRetriever()
    return _default_retriever


def retrieve_candidate_evidence(query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
    return get_retriever().retrieve_candidate_evidence(query=query, limit=top_k, **kwargs)


def retrieve_technical_knowledge(query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
    return get_retriever().retrieve_interview_knowledge(query=query, limit=top_k, **kwargs)


    def retrieve(
        self,
        query: str,
        store_type: str = "candidate",
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Generic dispatcher routing to candidate or interview knowledge store."""
        if store_type == "interview" or store_type == "technical":
            return self.retrieve_interview_knowledge(query=query, limit=limit, filters=filters)
        return self.retrieve_candidate_evidence(query=query, limit=limit, filters=filters)
