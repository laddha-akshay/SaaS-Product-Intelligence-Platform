from typing import List
from rank_bm25 import BM25Okapi


class SparseRetriever:
    def __init__(self, documents: List[str]):
        tokenized = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        self.documents = documents

    def search(self, query: str, top_k: int = 50):
        scores = self.bm25.get_scores(query.split())
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        return [
            {"text": self.documents[i], "score": float(score)} for i, score in ranked
        ]
