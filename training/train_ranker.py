"""Training pipeline for continuous model improvement."""
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from app.ranking.features import FeatureExtractor
from app.ranking.model import LambdaRankModel
from app.feedback import FeedbackCollector

class TrainingPipeline:
    """Generates training data from feedback and retrains ranking model."""
    
    def __init__(self, model_dir: str = "models", min_feedback: int = 50):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.min_feedback = min_feedback
        self.feature_extractor = FeatureExtractor()
        self.feedback = FeedbackCollector()
    
    def generate_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        Generate training data from feedback logs.
        
        Returns:
            (X, y, group_sizes) for LambdaRank training
            - X: feature matrix [n_samples, 6]
            - y: NDCG scores [n_samples]
            - group_sizes: queries per group for pairwise ranking
        """
        logs = self.feedback.load_feedback_logs(limit=10000)
        
        if len(logs) < self.min_feedback:
            print(f"Insufficient feedback: {len(logs)} < {self.min_feedback}")
            return None
        
        # Group by query
        queries_data = {}
        for log in logs:
            query = log.get("query")
            if query not in queries_data:
                queries_data[query] = []
            
            # Generate label based on feedback
            helpful = log.get("user_feedback", {}).get("helpful", False)
            confidence = log.get("confidence", 0.5)
            refused = log.get("refused", False)
            
            # NDCG score: high if helpful, low if refused
            ndcg_score = float(helpful) * confidence * (0 if refused else 1)
            
            queries_data[query].append({
                "text": log.get("answer"),
                "citations": log.get("citations", []),
                "confidence": confidence,
                "ndcg_score": ndcg_score
            })
        
        # Build feature matrix
        X_list, y_list, group_sizes = [], [], []
        
        for query, results in queries_data.items():
            if len(results) < 2:
                continue  # Need at least 2 results per query for ranking
            
            for result in results:
                # Mock features (in production, would re-extract from documents)
                features = np.array([
                    result["confidence"],  # dense_score
                    result["confidence"] * 0.9,  # sparse_score
                    len(result.get("text", "")) / 100,  # normalized_doc_length
                    len(result.get("citations", [])) / 3,  # term_overlap_ratio
                    0.9,  # recency_decay (mock)
                    float(result["ndcg_score"])  # feedback_signal
                ], dtype=np.float32)
                X_list.append(features)
                y_list.append(result["ndcg_score"])
            
            group_sizes.append(len(results))
        
        if not X_list:
            return None
        
        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.float32)
        
        return X, y, group_sizes
    
    def train_and_save(self, epochs: int = 100) -> bool:
        """
        Train ranker on feedback data and save model.
        
        Returns:
            True if training successful, False otherwise
        """
        data = self.generate_training_data()
        if data is None:
            return False
        
        X, y, group_sizes = data
        
        print(f"Training on {len(X)} samples from {len(group_sizes)} queries")
        
        model = LambdaRankModel()
        model.train(X, y, group_sizes, epochs=epochs)
        
        # Save model with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_path = self.model_dir / f"ranker_{timestamp}.pkl"
        model.save(model_path)
        
        print(f"Model saved to {model_path}")
        
        # Log training event
        training_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_path": str(model_path),
            "n_samples": len(X),
            "n_groups": len(group_sizes),
            "epochs": epochs,
            "features_mean": X.mean(axis=0).tolist(),
            "labels_mean": float(y.mean()),
            "labels_std": float(y.std())
        }
        
        log_path = self.model_dir / "training_log.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(training_log) + '\n')
        
        return True

if __name__ == "__main__":
    pipeline = TrainingPipeline()
    success = pipeline.train_and_save()
    
    if success:
        print("Training completed successfully")
    else:
        print("Training failed or insufficient data")

