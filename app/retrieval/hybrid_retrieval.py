class HybridRetriever:
    def __init__(self, dense, sparse):
        self.dense = dense
        self.sparse = sparse

    def search(self, query):
        d = self.dense.search(query)
        s = self.sparse.search(query)
        merged = {}
        for r in d + s:
            merged[r["text"]] = merged.get(r["text"], 0) + r["score"]
        return [
            {"text": t, "score": s}
            for t, s in sorted(merged.items(), key=lambda x: x[1], reverse=True)
        ]
