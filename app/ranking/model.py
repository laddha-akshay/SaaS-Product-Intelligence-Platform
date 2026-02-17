"""Learning-to-Rank model (LightGBM LambdaRank)."""
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class LambdaRankModel:
    """LightGBM LambdaRank model for ranking candidates by usefulness."""

    def __init__(self, model_path: str = "models/ranker.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.version = "v1"  # IMPORTANT for tests
        self.created_at = datetime.utcnow().isoformat()
        self.load_or_init()

    def load_or_init(self):
        """Load model from disk or initialize stub."""
        if self.model_path.exists() and LIGHTGBM_AVAILABLE:
            try:
                self.model = lgb.Booster(model_file=str(self.model_path))
                self.version = "v1"
                self.created_at = datetime.utcnow().isoformat()
            except Exception as e:
                print(f"Failed to load ranker: {e}. Using fallback.")
                self.model = None

    def rank(self, features: np.ndarray) -> np.ndarray:
        """
        Rank candidates using the model.
        Returns scores in descending order.
        """
        if self.model is not None and LIGHTGBM_AVAILABLE:
            scores = self.model.predict(features)
        else:
            # fallback weighted ranking
            # Weights: dense_score, sparse_score, doc_len, term_overlap, recency, feedback
            weights = np.array([0.45, 0.35, 0.01, 0.1, 0.05, 0.04], dtype=np.float32)
            scores = features @ weights

        # Return scores in descending order
        return np.array(sorted(scores, reverse=True))

    def train(
        self, X: np.ndarray, y: np.ndarray, group_sizes: List[int], epochs: int = 100
    ):
        """Train LambdaRank model."""
        if not LIGHTGBM_AVAILABLE:
            print("LightGBM not available. Skipping training.")
            return

        train_data = lgb.Dataset(X, label=y, group=group_sizes)
        params = {
            "objective": "lambdarank",
            "metric": "ndcg",
            "learning_rate": 0.05,
            "num_leaves": 31,
            "verbose": -1,
        }

        self.model = lgb.train(params, train_data, num_boost_round=epochs)
        self.version = "v1"
        self.created_at = datetime.utcnow().isoformat()
        self.save()

    def save(self):
        """Save model."""
        if self.model is not None and LIGHTGBM_AVAILABLE:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            self.model.save_model(str(self.model_path))

    # IMPORTANT: tests expect metadata()
    def metadata(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "path": str(self.model_path),
            "available": self.model is not None,
        }
