"""Configuration constants."""
# Retrieval
TOP_K = 5
DOC_PATH = "data/unstructured/internal_docs.md"
DENSE_MODEL = "all-MiniLM-L6-v2"

# LLM Reasoning
CONFIDENCE_THRESHOLD = 0.5
MAX_TOKENS = 256

# Monitoring
LATENCY_BASELINE_MS = 300
RECALL_BASELINE = 0.75
REFUSAL_BASELINE = 0.08

# App
APP_NAME = "SaaS-Product-Intelligence"
DEBUG = False
