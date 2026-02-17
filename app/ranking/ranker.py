"""Ranking orchestration."""
import numpy as np
from typing import List, Dict, Any
from app.ranking.features import FeatureExtractor
from app.ranking.model import LambdaRankModel

class RankingOrchestrator:
    """Orchestrates retrieval candidates through ranking."""
    
    def __init__(self):
        self.model = LambdaRankModel()
        self.feature_extractor = FeatureExtractor()
    
    def rank_candidates(self, query: str, candidates: List[Dict[str, Any]], 
                       top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rank candidates by usefulness.
        
        Args:
            query: user query
            candidates: list of {"text": ..., "score": ...} dicts from retrieval
            top_k: return top k candidates
        
        Returns:
            ranked candidates with rank scores
        """
        if not candidates:
            return []
        
        # Extract features for each candidate
        docs = [c["text"] for c in candidates]
        dense_scores = [c.get("score", 0.5) for c in candidates]
        sparse_scores = [c.get("score", 0.5) for c in candidates]
        
        features = self.feature_extractor.extract_batch(query, docs, dense_scores, sparse_scores)
        
        # Rank using model
        rank_scores = self.model.rank(features)
        
        # Attach rank scores and sort
        ranked = []
        for i, cand in enumerate(candidates):
            cand_copy = cand.copy()
            cand_copy["rank_score"] = float(rank_scores[i])
            ranked.append(cand_copy)
        
        ranked = sorted(ranked, key=lambda x: x["rank_score"], reverse=True)
        return ranked[:top_k]

def simple_rank(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy simple ranking function."""
    for d in docs:
        d["rank_score"] = d.get("score", 0.5)
    return sorted(docs, key=lambda x: x["rank_score"], reverse=True)

