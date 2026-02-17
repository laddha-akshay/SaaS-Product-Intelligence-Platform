"""Tests for ranking layer."""
import pytest
import numpy as np
from app.ranking.features import FeatureExtractor
from app.ranking.model import LambdaRankModel

@pytest.fixture
def feature_extractor():
    return FeatureExtractor()

@pytest.fixture
def sample_candidates():
    return [
        {"text": "onboarding change in March", "score": 0.85},
        {"text": "activation metrics report", "score": 0.72},
        {"text": "release notes v2.3", "score": 0.65}
    ]

def test_feature_extraction(feature_extractor, sample_candidates):
    """Test feature extraction produces correct dimensions."""
    query = "why did activation drop"
    features_list = []
    
    for doc in sample_candidates:
        features = feature_extractor.extract_features(
            query=query,
            doc=doc["text"],
            dense_score=doc["score"],
            sparse_score=doc["score"] * 0.9,
            recency_decay=0.95,
            feedback_signal=0.5
        )
        features_list.append(features)
    
    # Should have 6 dimensions
    assert len(features_list[0]) == 6
    assert all(isinstance(f, (int, float, np.number)) for f in features_list[0])

def test_ranking_model_initialization():
    """Test ranking model can be initialized."""
    model = LambdaRankModel()
    assert model is not None
    assert model.metadata()["version"] == "v1"

def test_ranking_model_fallback():
    """Test ranking model gracefully falls back to weighted ranking."""
    model = LambdaRankModel()
    features = np.array([
        [0.85, 0.75, 100, 0.6, 0.95, 0.5],
        [0.72, 0.65, 150, 0.4, 0.90, 0.3],
        [0.65, 0.58, 80, 0.5, 0.85, 0.2]
    ], dtype=np.float32)
    
    scores = model.rank(features)
    assert len(scores) == 3
    assert all(isinstance(s, (int, float, np.number)) for s in scores)
    # Should be sorted descending
    assert scores[0] >= scores[1] >= scores[2]

