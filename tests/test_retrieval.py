"""Tests for retrieval layer."""
import pytest
from app.retrieval.dense_retrieval import DenseRetriever
from app.retrieval.sparse_retrieval import SparseRetriever
from app.retrieval.hybrid_retrieval import HybridRetriever

@pytest.fixture
def sample_docs():
    return [
        "User activation drop by 20% in March after onboarding redesign",
        "Release 2.3 included changes to the onboarding flow",
        "Retention improved after fixing checkout bug in April",
        "Database migration completed successfully"
    ]

def test_dense_retrieval_initialization(sample_docs):
    """Test dense retriever can initialize."""
    retriever = DenseRetriever(sample_docs)
    assert retriever is not None
    assert len(retriever.docs) == len(sample_docs)

def test_dense_retrieval_search(sample_docs):
    """Test dense retrieval returns results."""
    retriever = DenseRetriever(sample_docs)
    results = retriever.search("onboarding activation")
    assert len(results) > 0
    assert all("text" in r and "score" in r for r in results)

def test_sparse_retrieval_initialization(sample_docs):
    """Test sparse retriever can initialize."""
    retriever = SparseRetriever(sample_docs)
    assert retriever is not None

def test_sparse_retrieval_search(sample_docs):
    """Test sparse retrieval returns results."""
    retriever = SparseRetriever(sample_docs)
    results = retriever.search("onboarding")
    assert len(results) > 0
    assert all("text" in r and "score" in r for r in results)

def test_hybrid_retrieval(sample_docs):
    """Test hybrid retrieval combines dense and sparse."""
    dense = DenseRetriever(sample_docs)
    sparse = SparseRetriever(sample_docs)
    hybrid = HybridRetriever(dense, sparse)
    
    results = hybrid.search("onboarding")
    assert len(results) > 0
    # Hybrid should return merged results
    assert all("text" in r and "score" in r for r in results)

