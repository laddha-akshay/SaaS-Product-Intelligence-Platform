"""Tests for end-to-end pipeline."""
import pytest
from app.pipeline import run_pipeline


def test_pipeline_basic_query():
    """Test pipeline handles basic query."""
    result = run_pipeline("What happened in March?")

    assert "answer" in result
    assert "citations" in result
    assert "confidence" in result
    assert "refused" in result
    assert "latency_ms" in result
    assert "query_id" in result


def test_pipeline_response_format():
    """Test pipeline returns proper response format."""
    result = run_pipeline("Why did activation drop?")

    # Validate response structure
    assert isinstance(result["citations"], list)
    assert isinstance(result["confidence"], float)
    assert isinstance(result["refused"], bool)
    assert isinstance(result["latency_ms"], float)
    assert result["latency_ms"] >= 0


def test_pipeline_with_refusal():
    """Test pipeline can refuse when confidence low."""
    # Query about something not in docs should potentially refuse
    result = run_pipeline("Tell me about quantum physics")

    assert "refused" in result
    # If refused, confidence should be low
    if result["refused"]:
        assert result["confidence"] < 0.7


def test_pipeline_error_handling():
    """Test pipeline handles errors gracefully."""
    # Empty query should still return valid response
    result = run_pipeline("")

    assert "query_id" in result
    assert "refused" in result
    assert "latency_ms" in result
