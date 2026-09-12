import pytest
from careerpilot.rag.embeddings import (
    BaseEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    MockEmbeddingProvider,
    get_embedding_provider,
)


def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimension=384)
    assert provider.dimension == 384

    # Single text embedding
    vec = provider.embed_text("Test query about Python and SQL")
    assert isinstance(vec, list)
    assert len(vec) == 384
    # Check consistency
    vec2 = provider.embed_text("Test query about Python and SQL")
    assert vec == vec2

    # Batch embedding
    docs = ["Python data engineering", "BigQuery optimization"]
    vectors = provider.embed_documents(docs)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


def test_get_embedding_provider_factory():
    mock_prov = get_embedding_provider(provider_type="mock")
    assert isinstance(mock_prov, MockEmbeddingProvider)
    assert mock_prov.dimension == 384


def test_sentence_transformer_provider_or_fallback():
    # If SentenceTransformer can be initialized or falls back safely
    provider = get_embedding_provider()
    assert isinstance(provider, BaseEmbeddingProvider)
    assert provider.dimension > 0

    vec = provider.embed_text("Candidate has GCP and BigQuery experience")
    assert len(vec) == provider.dimension
