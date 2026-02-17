"""Feature engineering for ranking model."""
import numpy as np
from typing import List, Dict, Any

class FeatureExtractor:
    """Extracts features for LambdaRank model."""
    
    @staticmethod
    def extract_features(query: str, document: str, dense_score: float, sparse_score: float, 
                        recency_decay: float = 1.0, feedback_signal: float = 0.5) -> np.ndarray:
        """
        Extract ranking features.
        
        Features:
        0. Dense similarity score (semantic)
        1. Sparse similarity score (keyword)
        2. Document length (longer docs may be more informative)
        3. Query-doc term overlap (keyword density)
        4. Recency decay (fresher docs are better)
        5. Feedback signal (historical usefulness)
        """
        features = [
            dense_score,
            sparse_score,
            min(1.0, len(document.split()) / 500.0),  # normalized doc length
            len(set(query.lower().split()) & set(document.lower().split())) / max(len(query.split()), 1),
            recency_decay,
            feedback_signal
        ]
        return np.array(features, dtype=np.float32)
    
    @staticmethod
    def extract_batch(query: str, documents: List[str], dense_scores: List[float], 
                     sparse_scores: List[float]) -> np.ndarray:
        """Extract features for a batch of documents."""
        features_list = []
        for doc, ds, ss in zip(documents, dense_scores, sparse_scores):
            feat = FeatureExtractor.extract_features(query, doc, ds, ss)
            features_list.append(feat)
        return np.array(features_list, dtype=np.float32)

