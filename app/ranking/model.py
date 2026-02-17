"""Learning-to-Rank model (LightGBM LambdaRank)."""
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

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
        self.version = None
        self.created_at = None
        self.load_or_init()
    
    def load_or_init(self):
        """Load model from disk or initialize stub."""
        if self.model_path.exists() and LIGHTGBM_AVAILABLE:
            try:
                self.model = lgb.Booster(model_file=str(self.model_path))
                self.version = self.model_path.stat().st_mtime
                self.created_at = datetime.fromtimestamp(self.version).isoformat()
            except Exception as e:
                print(f"Failed to load ranker: {e}. Using fallback.")
                self.model = None
        else:
            self.model = None
            self.version = "1.0"
            self.created_at = datetime.utcnow().isoformat()
    
    def rank(self, features: np.ndarray) -> np.ndarray:
        """
        Rank candidates using the model.
        
        Args:
            features: (n_candidates, n_features) array
        
        Returns:
            scores: (n_candidates,) array of ranking scores
        """
        if self.model is not None and LIGHTGBM_AVAILABLE:
            return self.model.predict(features)
        else:
            # Fallback: simple weighted combination of features
            # weights = [dense=0.4, sparse=0.3, length=0.1, overlap=0.1, recency=0.05, feedback=0.05]
            weights = np.array([0.4, 0.3, 0.1, 0.1, 0.05, 0.05])
            return np.dot(features, weights)
    
    def train(self, X: np.ndarray, y: np.ndarray, group_sizes: List[int], epochs: int = 100):
        """Train LambdaRank model on labeled data."""
        if not LIGHTGBM_AVAILABLE:
            print("LightGBM not available. Skipping training.")
            return
        
        try:
            train_data = lgb.Dataset(X, label=y, group=group_sizes)
            params = {
                'objective': 'lambdarank',
                'metric': 'ndcg',
                'ndcg_eval_at': [1, 3, 5],
                'learning_rate': 0.05,
                'num_leaves': 31,
                'verbose': -1
            }
            self.model = lgb.train(params, train_data, num_boost_round=epochs)
            self.version = datetime.utcnow().isoformat()
            self.created_at = self.version
            self.save()
            print(f"Ranker trained and saved to {self.model_path}")
        except Exception as e:
            print(f"Training failed: {e}")
    
    def save(self):
        """Save model to disk."""
        if self.model is not None and LIGHTGBM_AVAILABLE:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            self.model.save_model(str(self.model_path))
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata for versioning."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "path": str(self.model_path),
            "available": self.model is not None
        }

