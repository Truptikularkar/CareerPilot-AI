from careerpilot.rag.retriever import DualStoreRetriever
from careerpilot.rag.embeddings import get_embedding_provider


def run_query_demonstration():
    """Runs test queries demonstrating isolated retrieval across both stores."""
    print("=" * 70)
    print("  CareerPilot AI: Dual-Store RAG Retrieval Demonstration")
    print("=" * 70)

    retriever = DualStoreRetriever()

    test_cases = [
        {
            "query": "How did the candidate optimize BigQuery?",
            "store": "candidate",
            "description": "Candidate specific question -> should return verified Cognizant experience/project",
        },
        {
            "query": "What RAG project did the candidate build?",
            "store": "candidate",
            "description": "Candidate specific project question -> should return Local RAG Sandbox",
        },
        {
            "query": "What is reciprocal rank fusion?",
            "store": "interview",
            "description": "General conceptual interview question -> should return Technical Knowledge",
        },
        {
            "query": "Explain event-driven ingestion architecture on GCP",
            "store": "interview",
            "description": "General architecture interview question -> should return Technical Knowledge",
        },
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n--- [Test Query {idx}] ---")
        print(f"Query:       \"{tc['query']}\"")
        print(f"Target Store: {tc['store'].upper()}")
        print(f"Intent:       {tc['description']}")
        print("-" * 50)

        if tc["store"] == "candidate":
            results = retriever.retrieve_candidate_evidence(tc["query"], limit=2)
        else:
            results = retriever.retrieve_interview_knowledge(tc["query"], limit=2)

        if not results:
            print("  [!] No results retrieved.")
        else:
            for r_idx, r in enumerate(results, 1):
                print(f"  Result #{r_idx}:")
                print(f"    Chunk ID:        {r.chunk_id}")
                print(f"    Source:          {r.source}")
                print(f"    Evidence Status: {r.evidence_status}")
                print(f"    Distance:        {r.distance:.4f}")
                print(f"    Text Preview:    {r.text[:120]}...")

    print("\n" + "=" * 70)
    print("Dual-store retrieval demonstration completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_query_demonstration()
