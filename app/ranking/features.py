"""Feature engineering for ranking model."""
import numpy as np
from typing import List


class FeatureExtractor:
    """Extracts features for LambdaRank model."""

    @staticmethod
    def extract_features(
        query: str,
        doc: str,
        dense_score: float,
        sparse_score: float,
        recency_decay: float = 1.0,
        feedback_signal: float = 0.5,
    ) -> np.ndarray:
        """
        Extract ranking features.

        Features:
        0. Dense similarity score
        1. Sparse similarity score
        2. Document length
        3. Query-doc term overlap
        4. Recency decay
        5. Feedback signal
        """

        features = [
            dense_score,
            sparse_score,
            min(1.0, len(doc.split()) / 500.0),
            len(set(query.lower().split()) & set(doc.lower().split()))
            / max(len(query.split()), 1),
            recency_decay,
            feedback_signal,
        ]

        return np.array(features, dtype=np.float32)

    @staticmethod
    def extract_batch(
        query: str,
        documents: List[str],
        dense_scores: List[float],
        sparse_scores: List[float],
    ) -> np.ndarray:
        """Extract features for a batch of documents."""
        features_list = []
        for doc, ds, ss in zip(documents, dense_scores, sparse_scores):
            feat = FeatureExtractor.extract_features(query, doc, ds, ss)
            features_list.append(feat)
        return np.array(features_list, dtype=np.float32)
