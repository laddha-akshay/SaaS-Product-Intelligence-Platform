def load_docs(path):
    with open(path) as f:
        return [l.strip() for l in f.readlines() if l.strip()]
"""Minimal ingestion module."""
def ingest_sources():
    return {"sources": []}
