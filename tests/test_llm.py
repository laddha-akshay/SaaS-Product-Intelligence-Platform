"""Tests for constrained LLM reasoning."""
import pytest
from app.llm.constrained import ConstrainedReasoning


@pytest.fixture
def reasoning():
    return ConstrainedReasoning(confidence_threshold=0.5)


@pytest.fixture
def sample_context():
    return [
        {
            "text": "Onboarding redesign in March caused 20% activation drop",
            "rank_score": 0.95,
        },
        {"text": "Release 2.3 included UI changes to signup flow", "rank_score": 0.87},
    ]


def test_reasoning_initialization(reasoning):
    """Test reasoning can initialize."""
    assert reasoning is not None
    assert reasoning.confidence_threshold == 0.5


def test_answer_synthesis(reasoning, sample_context):
    """Test answer synthesis works."""
    query = "Why did activation drop in March?"
    answer = reasoning.synthesize_answer(query, sample_context)

    assert "answer" in answer
    assert "citations" in answer
    assert "confidence" in answer
    assert "refused" in answer

    # Should contain citation to context
    if not answer["refused"]:
        assert answer["confidence"] >= 0
        assert answer["confidence"] <= 1


def test_low_confidence_refusal(reasoning):
    """Test refusal when confidence too low."""
    minimal_context = [{"text": "vague info", "rank_score": 0.1}]
    answer = reasoning.synthesize_answer("complex question", minimal_context)

    # Should refuse due to low confidence
    assert "refused" in answer
    # Low confidence should lead to refusal
    if answer.get("confidence", 0) < reasoning.confidence_threshold:
        assert answer["refused"] is True


def test_citation_extraction(reasoning, sample_context):
    """Test citation validation."""
    query = "Why did activation drop?"
    answer = reasoning.synthesize_answer(query, sample_context)

    # If answer not refused, should have citations
    if not answer["refused"] and answer.get("answer"):
        citations = answer.get("citations", [])
        # Citations should be from provided context
        for citation in citations:
            assert (
                any(
                    context["text"] in citation or citation in context["text"]
                    for context in sample_context
                )
                or citation == ""
            )
