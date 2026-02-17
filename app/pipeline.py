"""Core pipeline orchestration."""
import time
import uuid
from typing import Dict, Any, List
from app.ingestion import load_docs
from app.retrieval.dense_retrieval import DenseRetriever
from app.retrieval.sparse_retrieval import SparseRetriever
from app.retrieval.hybrid_retrieval import HybridRetriever
from app.ranking.ranker import RankingOrchestrator
from app.llm.constrained import ConstrainedReasoning
from app.feedback import FeedbackCollector
from app.monitoring import MetricsCollector
from app.config import DOC_PATH, TOP_K

# Initialize components
docs = load_docs(DOC_PATH)
dense = DenseRetriever(docs)
sparse = SparseRetriever(docs)
hybrid = HybridRetriever(dense, sparse)
ranker = RankingOrchestrator()
reasoning = ConstrainedReasoning(confidence_threshold=0.5)
feedback_collector = FeedbackCollector()
metrics = MetricsCollector()


def run_pipeline(query: str) -> Dict[str, Any]:
    """
    Full pipeline: retrieve → rank → reason → collect feedback.

    Args:
        query: user query

    Returns:
        {
            "answer": str or None,
            "citations": List[str],
            "confidence": float,
            "refused": bool,
            "latency_ms": float,
            "query_id": str
        }
    """
    query_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        # Step 1: Retrieve candidates (maximize recall)
        candidates = hybrid.search(query)

        # Step 2: Rank by usefulness (LambdaRank)
        ranked = ranker.rank_candidates(query, candidates, top_k=TOP_K)

        # Step 3: Synthesize answer with constraints
        answer = reasoning.synthesize_answer(query, ranked)

        # Step 4: Log metrics
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_query(
            query_id=query_id,
            latency_ms=latency_ms,
            retrieval_recall=min(1.0, len(candidates) / max(len(docs), 1)),
            ranker_ndcg=sum(r.get("rank_score", 0) for r in ranked)
            / max(len(ranked), 1),
            llm_refused=answer.get("refused", False),
            confidence=answer.get("confidence", 0.0),
        )

        # Log interaction
        feedback_collector.log_interaction(query, answer)

        return {
            "query_id": query_id,
            "answer": answer.get("answer"),
            "citations": answer.get("citations", []),
            "confidence": answer.get("confidence", 0.0),
            "refused": answer.get("refused", False),
            "latency_ms": latency_ms,
        }

    except Exception as e:
        print(f"Pipeline error: {e}")
        return {
            "query_id": query_id,
            "answer": None,
            "citations": [],
            "confidence": 0.0,
            "refused": True,
            "error": str(e),
            "latency_ms": (time.time() - start_time) * 1000,
        }
