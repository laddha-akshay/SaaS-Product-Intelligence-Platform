from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class DenseRetriever:
    def __init__(self, docs):
        self.docs = docs
        emb = model.encode(docs, normalize_embeddings=True)
        self.index = faiss.IndexFlatIP(emb.shape[1])
        self.index.add(emb)
        self.emb = emb

    def search(self, query, k=50):
        q = model.encode([query], normalize_embeddings=True)
        s, idx = self.index.search(q, k)
        return [{"text":self.docs[i],"score":float(s[0][j])} for j,i in enumerate(idx[0])]
