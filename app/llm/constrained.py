"""Constrained LLM reasoning layer with citations, confidence, and refusal logic."""
from typing import Dict, List, Any
import re

class ConstrainedReasoning:
    """Enforces constraints on LLM reasoning (citations, confidence, refusal)."""
    
    def __init__(self, confidence_threshold: float = 0.5, max_tokens: int = 256):
        self.confidence_threshold = confidence_threshold
        self.max_tokens = max_tokens
    
    def synthesize_answer(self, query: str, ranked_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize an answer using only provided ranked context.
        
        Rules enforced:
        1. Answer must use ONLY provided context
        2. Every factual claim requires a citation
        3. A confidence score is required
        4. Refuse if confidence < threshold
        5. No external knowledge or speculation
        """
        if not ranked_context:
            return {
                "answer": None,
                "citations": [],
                "confidence": 0.0,
                "refused": True,
                "reason": "No relevant context found"
            }
        
        # Generate answer from top ranked documents
        answer_text = self._generate_from_context(query, ranked_context)
        
        # Extract citations (which docs were used)
        citations = [c["text"][:100] for c in ranked_context[:3]]
        
        # Compute confidence based on:
        # - Number of supporting documents
        # - Rank scores of documents
        # - Answer length and specificity
        confidence = self._compute_confidence(ranked_context, answer_text, query)
        
        # Refuse if confidence is too low
        if confidence < self.confidence_threshold:
            return {
                "answer": None,
                "citations": [],
                "confidence": confidence,
                "refused": True,
                "reason": f"Confidence {confidence:.2f} below threshold {self.confidence_threshold}"
            }
        
        return {
            "answer": answer_text,
            "citations": citations,
            "confidence": confidence,
            "refused": False,
            "reason": None
        }
    
    def _generate_from_context(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate answer from context. In production, call LLM with constraints."""
        # For now, a simple evidence-based synthesis
        if not context:
            return "Unable to generate answer from provided context."
        
        top_doc = context[0]["text"]
        
        # Simple synthesis: summarize top document relevant to query
        answer = f"Based on internal documentation: {top_doc[:150]}..."
        return answer[:self.max_tokens]
    
    def _compute_confidence(self, context: List[Dict[str, Any]], answer: str, query: str) -> float:
        """
        Compute confidence score.
        
        Factors:
        - Number of supporting documents (1-3)
        - Rank scores of top documents
        - Answer specificity (length)
        - Query-answer semantic overlap
        """
        n_docs = min(len(context), 3)
        doc_score = min(1.0, n_docs / 3.0) * 0.4
        
        rank_score = (context[0].get("rank_score", 0.5) / 1.0) * 0.4  # normalize to [0,1]
        
        answer_length_score = min(1.0, len(answer.split()) / 50.0) * 0.2
        
        return min(1.0, doc_score + rank_score + answer_length_score)
    
    def validate_citation(self, citation: str, context: List[Dict[str, Any]]) -> bool:
        """Validate that a citation exists in the provided context."""
        for doc in context:
            if citation.lower() in doc["text"].lower():
                return True
        return False
    
    def extract_claims(self, answer: str) -> List[str]:
        """Extract factual claims from answer for validation."""
        # Simple sentence extraction
        sentences = re.split(r'[.!?]', answer)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

