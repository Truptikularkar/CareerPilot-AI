import sys
from pathlib import Path
from careerpilot.core.logging import get_logger
from careerpilot.rag.candidate_store import CandidateStore
from careerpilot.rag.interview_store import InterviewStore
from careerpilot.rag.embeddings import get_embedding_provider

logger = get_logger("careerpilot.rag.build_index")


def build_dual_index(candidate_dir: Path = Path("data/candidate"), knowledge_dir: Path = Path("data/knowledge/interview")):
    """Builds and indexes both Candidate Evidence Store and Interview Knowledge Store."""
    print("=" * 60)
    print("  CareerPilot AI: Building Dual-Store RAG Index")
    print("=" * 60)

    embedding_provider = get_embedding_provider()
    print(f"Embedding Provider: {embedding_provider.__class__.__name__} (dim={embedding_provider.dimension})")

    # 1. Index Candidate Evidence Store
    print("\n[1/2] Indexing Candidate Evidence Store...")
    cand_store = CandidateStore(embedding_provider=embedding_provider)
    cand_files = list(candidate_dir.glob("*.*")) if candidate_dir.exists() else []
    cand_chunks = cand_store.index_candidate_data(candidate_dir=candidate_dir, clear_existing=True)

    # 2. Index Interview Knowledge Store
    print("[2/2] Indexing Interview & Technical Knowledge Store...")
    interview_store = InterviewStore(embedding_provider=embedding_provider)
    interview_files = list(knowledge_dir.glob("*.md")) if knowledge_dir.exists() else []
    interview_chunks = interview_store.index_interview_data(knowledge_dir=knowledge_dir, clear_existing=True)

    print("\n" + "=" * 60)
    print("  Index Summary")
    print("=" * 60)
    print(f"Candidate documents indexed: {len(cand_files)}")
    print(f"Candidate chunks: {cand_chunks}")
    print(f"Interview documents indexed: {len(interview_files)}")
    print(f"Interview chunks: {interview_chunks}")
    print("=" * 60)
    print("Dual-store ChromaDB indexing completed successfully!\n")

    return {
        "candidate_documents": len(cand_files),
        "candidate_chunks": cand_chunks,
        "interview_documents": len(interview_files),
        "interview_chunks": interview_chunks,
    }


if __name__ == "__main__":
    build_dual_index()
