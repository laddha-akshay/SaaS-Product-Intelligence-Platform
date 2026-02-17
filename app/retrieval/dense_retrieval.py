"""Dense retriever with lazy imports and a lightweight fallback for tests.

This module avoids importing heavy ML libraries (transformers/tensorflow/faiss)
at import time. If `sentence_transformers` and `faiss` are available they will be
used; otherwise a deterministic numpy-based embedding + brute-force search is
used so unit tests can run in minimal environments.
"""

import hashlib
from typing import List, Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None  # type: ignore

try:
    import faiss  # type: ignore
except Exception:
    faiss = None  # type: ignore


def _deterministic_embedding(text: str, dim: int = 384) -> np.ndarray:
    """Create a deterministic pseudo-embedding for `text` using a hash-seeded RNG.

    This is intentionally lightweight and deterministic so tests get stable
    behavior without needing real model binaries.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "little")
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    v /= np.linalg.norm(v) + 1e-12
    return v


class DenseRetriever:
    def __init__(self, docs: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dim: int = 384):
        self.docs = docs
        self.dim = dim
        self._model: Optional[object] = None
        self._use_real_model = False

        # Try to instantiate the real model lazily. Failures fall back to deterministic embeddings.
        if SentenceTransformer is not None:
            try:
                self._model = SentenceTransformer(model_name)
                self._use_real_model = True
            except Exception:
                self._model = None
                self._use_real_model = False

        # Build embeddings (either real model or deterministic fallback)
        if self._use_real_model:
            emb = self._model.encode(docs, normalize_embeddings=True)
            emb = np.asarray(emb, dtype=np.float32)
        else:
            emb = np.vstack([_deterministic_embedding(d, dim=self.dim) for d in docs])

        self.emb = emb

        # If faiss is available and we used a real model, build an index for speed.
        if faiss is not None and self._use_real_model:
            self._index = faiss.IndexFlatIP(self.emb.shape[1])
            self._index.add(self.emb)
            self._use_faiss = True
        else:
            self._index = None
            self._use_faiss = False

    def _encode(self, texts: List[str]) -> np.ndarray:
        if self._use_real_model and self._model is not None:
            return np.asarray(self._model.encode(texts, normalize_embeddings=True), dtype=np.float32)
        return np.vstack([_deterministic_embedding(t, dim=self.dim) for t in texts])

    def search(self, query: str, k: int = 50):
        q = self._encode([query])
        if self._use_faiss and self._index is not None:
            s, idx = self._index.search(q, k)
            return [
                {"text": self.docs[i], "score": float(s[0][j])}
                for j, i in enumerate(idx[0])
            ]

        # Fallback: brute-force dot product search using numpy.
        sims = (self.emb @ q.T).flatten()
        k = min(k, len(sims))
        # select top k indices
        if k == 0:
            return []
        topk = np.argpartition(-sims, range(k))[:k]
        topk_sorted = topk[np.argsort(-sims[topk])]
        return [{"text": self.docs[i], "score": float(sims[i])} for i in topk_sorted]

