"""Smoke tests for system integration."""
import sys


def test_imports():
    """Test that core modules import without errors."""
    try:
        from app.ingestion import load_docs
        from app.config import TOP_K, DOC_PATH
        from app.data import DataValidator, DataLoader
        from app.feedback import FeedbackCollector

        print("✓ All imports successful")
        assert True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        assert False


def test_feedback_collector():
    """Test feedback collection functionality."""
    from app.feedback import FeedbackCollector

    collector = FeedbackCollector(log_path="/tmp/test_feedback.jsonl")

    # Log an interaction
    interaction_id = collector.log_interaction(
        query="Test query",
        answer={"answer": "Test answer", "confidence": 0.8, "citations": []},
        user_feedback=None,
    )

    assert interaction_id is not None
    print(f"✓ Logged interaction: {interaction_id}")

    # Log feedback
    collector.log_feedback(interaction_id, helpful=True, feedback="Good answer")

    # Get stats
    stats = collector.get_feedback_stats()
    assert stats["total_interactions"] >= 1
    print(f"✓ Feedback stats: {stats}")


def test_data_validator():
    """Test data validation."""
    from app.data import DataValidator

    validator = DataValidator()

    # Test valid structured data (should be a list of dicts with required keys)
    valid_data = [{"date": "2024-01-01", "metric": "activation", "value": 100}]
    result = validator.validate_structured_data(valid_data)
    assert result is True
    print("✓ Data validation passed")

    # Test invalid data (missing required keys)
    invalid_data = [{"name": "Test", "value": 100}]
    result = validator.validate_structured_data(invalid_data)
    assert result is False
    print("✓ Data validation correctly rejects invalid data")


def test_config():
    """Test configuration loads."""
    from app.config import TOP_K, DOC_PATH, CONFIDENCE_THRESHOLD

    assert TOP_K == 5
    assert CONFIDENCE_THRESHOLD == 0.5
    assert DOC_PATH is not None
    print(f"✓ Configuration loaded: TOP_K={TOP_K}, THRESHOLD={CONFIDENCE_THRESHOLD}")


if __name__ == "__main__":
    print("\n=== Running Smoke Tests ===\n")
    test_imports()
    test_config()
    test_data_validator()
    test_feedback_collector()
    print("\n=== All Smoke Tests Passed ===\n")
