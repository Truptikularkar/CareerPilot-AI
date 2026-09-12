import json
from pathlib import Path
import pytest
import chromadb
from chromadb.config import Settings as ChromaSettings

from careerpilot.rag.embeddings import MockEmbeddingProvider
from careerpilot.rag.vector_store import LocalVectorClient
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.rag.interview_store import InterviewStore
from careerpilot.rag.retriever import DualStoreRetriever, RetrievalResult


@pytest.fixture(scope="module")
def mock_embedding():
    return MockEmbeddingProvider(dimension=128)


@pytest.fixture(scope="module")
def ephemeral_chroma_client(tmp_path_factory):
    test_dir = tmp_path_factory.mktemp("test_vector_db")
    return LocalVectorClient(path=str(test_dir))



@pytest.fixture(scope="module")
def indexed_dual_stores(ephemeral_chroma_client, mock_embedding):
    cand_store = CandidateStore(
        embedding_provider=mock_embedding,
        client=ephemeral_chroma_client,
    )
    cand_dir = Path("data/candidate")
    cand_store.index_candidate_data(candidate_dir=cand_dir, clear_existing=True)

    interview_store = InterviewStore(
        embedding_provider=mock_embedding,
        client=ephemeral_chroma_client,
    )
    know_dir = Path("data/knowledge/interview")
    interview_store.index_interview_data(knowledge_dir=know_dir, clear_existing=True)

    return cand_store, interview_store


@pytest.fixture(scope="module")
def retriever(indexed_dual_stores, mock_embedding):
    cand_store, interview_store = indexed_dual_stores
    return DualStoreRetriever(
        candidate_store=cand_store,
        interview_store=interview_store,
        embedding_provider=mock_embedding,
    )


def test_candidate_store_indexing_and_chunking(indexed_dual_stores):
    cand_store, _ = indexed_dual_stores
    count = cand_store.count()
    assert count > 0, "Candidate store should contain indexed chunks"
    
    # Verify semantic chunks exist
    results = cand_store.collection.get(include=["metadatas", "documents"])
    assert len(results["ids"]) == count
    
    # Check that metadata fields are preserved
    sample_meta = results["metadatas"][0]
    assert "source_file" in sample_meta
    assert "evidence_status" in sample_meta
    assert "evidence_type" in sample_meta
    assert "verified" in sample_meta


def test_interview_store_indexing(indexed_dual_stores):
    _, interview_store = indexed_dual_stores
    count = interview_store.count()
    assert count > 0, "Interview store should contain indexed knowledge chunks"

    results = interview_store.collection.get(include=["metadatas"])
    sample_meta = results["metadatas"][0]
    assert "topic" in sample_meta
    assert "category" in sample_meta
    assert "difficulty" in sample_meta


def test_candidate_retrieval_with_grounding(retriever):
    # Query for candidate specific experience
    results = retriever.retrieve_candidate_evidence(
        query="How did the candidate optimize BigQuery query costs?",
        limit=3,
        evidence_status="SUPPORTED",
    )
    assert len(results) > 0
    for r in results:
        assert isinstance(r, RetrievalResult)
        assert r.evidence_status == "SUPPORTED"
        assert r.verified is True
        assert r.source in ["experience.md", "projects.md", "achievements.md", "skills.md", "profile.yaml", "evidence.json"]


def test_technical_knowledge_retrieval(retriever):
    # Query for general technical concept
    results = retriever.retrieve_interview_knowledge(
        query="What is reciprocal rank fusion?",
        limit=3,
    )
    assert len(results) > 0
    top_result = results[0]
    assert "rag.md" in top_result.source or top_result.metadata.get("topic") == "RAG"


def test_stores_remain_isolated(retriever):
    # Candidate query on interview store should NOT return candidate's private company names
    interview_res = retriever.retrieve_interview_knowledge("Cognizant Technology Solutions", limit=3)
    for r in interview_res:
        assert "Cognizant" not in r.text, "Technical interview store must not leak candidate company specifics"

    # Technical query on candidate store
    cand_res = retriever.retrieve_candidate_evidence("Explain Spark shuffle and broadcast joins", limit=3)
    for r in cand_res:
        # Candidate store must only return candidate-verified chunks, not pure general definitions
        assert "source_file" in r.metadata


def test_truth_guard_filters_unsupported_claims(indexed_dual_stores, retriever):
    cand_store, _ = indexed_dual_stores
    
    # Query specifically asking for verified evidence
    verified_results = retriever.retrieve_candidate_evidence(
        query="AWS production experience",
        limit=5,
        evidence_status="SUPPORTED",
    )
    # Ensure no claim stating AWS is supported for production appears
    for r in verified_results:
        assert r.evidence_status == "SUPPORTED"
        assert "AWS production experience" not in r.text or "NOT_SUPPORTED" not in r.text


def test_duplicate_indexing_is_idempotent(indexed_dual_stores, mock_embedding):
    cand_store, _ = indexed_dual_stores
    initial_count = cand_store.count()

    # Re-index without clearing (upsert)
    cand_dir = Path("data/candidate")
    second_count = cand_store.index_candidate_data(candidate_dir=cand_dir, clear_existing=False)
    
    assert cand_store.count() == initial_count, "Idempotent upsert should not inflate chunk count"


def test_retrieval_evaluation_dataset(retriever):
    eval_file = Path("data/knowledge/retrieval_eval.json")
    assert eval_file.exists()
    
    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    queries = eval_data.get("queries", [])
    assert len(queries) >= 10

    for item in queries:
        q = item["query"]
        store = item["expected_store"]

        if store == "candidate":
            results = retriever.retrieve_candidate_evidence(q, limit=3)
        else:
            results = retriever.retrieve_interview_knowledge(q, limit=3)

        assert len(results) > 0, f"Query '{q}' returned no results from {store} store"
        top_res = results[0]
        assert top_res.chunk_id != ""
