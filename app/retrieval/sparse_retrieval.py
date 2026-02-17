"""Sparse retriever with lazy imports and fallback.

This module avoids importing heavy dependencies at import time.
If rank_bm25 is available, it will be used; otherwise a simple
deterministic fallback using word frequency is used.
"""

from typing import List
import re

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None  # type: ignore


class SparseRetriever:
    def __init__(self, documents: List[str]):
        self.documents = documents
        tokenized = [self._tokenize(doc) for doc in documents]
        
        if BM25Okapi is not None:
            self.bm25 = BM25Okapi(tokenized)
            self._use_bm25 = True
        else:
            # Fallback: store tokenized docs and use word frequency
            self.tokenized_docs = tokenized
            self._use_bm25 = False
            self.bm25 = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenizer: lowercase, split on whitespace, remove punctuation."""
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return tokens

    def search(self, query: str, top_k: int = 50):
        """Search for documents matching the query."""
        if self._use_bm25 and self.bm25 is not None:
            scores = self.bm25.get_scores(self._tokenize(query))
        else:
            # Fallback: compute simple word overlap score
            query_tokens = set(self._tokenize(query))
            scores = []
            for doc_tokens in self.tokenized_docs:
                doc_token_set = set(doc_tokens)
                overlap = len(query_tokens & doc_token_set)
                score = overlap / max(len(query_tokens), 1)
                scores.append(score)
            scores = scores  # keep as list of floats

        # Rank and return top-k
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {"text": self.documents[i], "score": float(score)} for i, score in ranked
        ]
