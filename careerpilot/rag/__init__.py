"""
CareerPilot AI RAG Package
Dual-Store Retrieval-Augmented Generation for Candidate Evidence & Interview Knowledge
"""
from careerpilot.rag.embeddings import (
    BaseEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    MockEmbeddingProvider,
    get_embedding_provider,
)
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.rag.interview_store import InterviewStore
from careerpilot.rag.retriever import DualStoreRetriever, RetrievalResult

__all__ = [
    "BaseEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider",
    "CandidateStore",
    "InterviewStore",
    "DualStoreRetriever",
    "RetrievalResult",
]
