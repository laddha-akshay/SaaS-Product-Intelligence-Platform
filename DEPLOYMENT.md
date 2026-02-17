# SaaS Product Intelligence Platform - Deployment & Operations

## Architecture Overview

This is a **production ML system** that answers "Why did [metric] change?" using internal SaaS product data.

**Key Design Principles**:
- **Deterministic**: Decisions trace to retrieved documents
- **Interpretable**: All answers cite sources; confidence scores explained
- **Observable**: Full query-to-answer pipeline logged for debugging
- **Safe**: LLM constrained to never invent facts; refuses low-confidence queries
- **Evidence-Based**: Continuous feedback loops improve ranking, not retrieval

**Workflow**:
```
Query → [Dense Search] → [Sparse Search] → [Hybrid Merge]
   ↓
[Feature Engineering] → [LambdaRank Model] → [Top-K Ranking]
   ↓
[Constrained LLM] → [Citations + Confidence + Refusal Logic]
   ↓
[Metrics + Drift Detection] → [Feedback Logging]
   ↓
[Periodic Retraining] → [Model Versioning] → [Rollback Capability]
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- 2GB RAM (CPU inference)
- Docker (optional, for containerization)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repo>
   cd SaaS-Product-Intelligence-Platform
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   python run.py
   ```
   Server starts at `http://localhost:8000`

3. **Test**:
   ```bash
   pytest tests/ -v
   ```

### Docker Deployment

```bash
# Build
docker build -t saas-intelligence:latest .

# Run
docker run -p 8000:8000 saas-intelligence:latest

# Or with docker-compose
docker-compose up
```

---

## API Endpoints

### Query Endpoint
**POST** `/query`
```json
{
  "query": "Why did user activation drop in March?"
}
```
**Response**:
```json
{
  "query_id": "uuid...",
  "answer": "The onboarding redesign in Release 2.3 caused a 20% activation drop due to...",
  "citations": [
    "Onboarding redesign in March caused 20% activation drop",
    "Release 2.3 included UI changes to signup flow"
  ],
  "confidence": 0.87,
  "refused": false,
  "latency_ms": 245
}
```

### Health Check
**GET** `/health`
```json
{
  "status": "ok|degraded",
  "uptime_seconds": 3600,
  "drift_detected": false,
  "message": "System operational"
}
```

### Metrics
**GET** `/metrics`
```json
{
  "p95_latency_ms": 450,
  "retrieval_recall_mean": 0.82,
  "ranker_ndcg_mean": 0.78,
  "llm_refused_rate": 0.08,
  "confidence_mean": 0.75
}
```

### Feedback Submission
**POST** `/feedback`
```json
{
  "query_id": "uuid...",
  "helpful": true,
  "feedback": "Answer was accurate and well-cited"
}
```

### Feedback Stats
**GET** `/feedback/stats`
```json
{
  "total_interactions": 1250,
  "helpful_rate": 0.82,
  "feedback_rate": 0.45,
  "refused_rate": 0.08,
  "avg_confidence": 0.76
}
```

---

## Monitoring & Alerting

### Key Metrics

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| P95 Latency | 300ms | > 1000ms |
| Retrieval Recall | 0.75 | < 0.65 |
| Ranking NDCG | 0.78 | < 0.70 |
| Refusal Rate | 0.08 | > 0.15 |
| Confidence | 0.75 | < 0.65 |

### Drift Detection

System automatically monitors for distribution shifts:

```python
from app.monitoring import HealthCheck

health = HealthCheck()
status = health.get_health()
if status["drift_detected"]:
    print("⚠️ Metrics degraded - check system")
```

**Drift triggers**:
- P95 latency > 1000ms (performance issue)
- Recall mean < 0.65 (retrieval quality drop)
- Refusal rate > 0.15 (confidence crisis)

**Actions**:
1. Review recent data/query patterns
2. Check model performance on validation set
3. Trigger retraining if drift confirmed
4. Rollback to previous model if needed

---

## Continuous Improvement

### Feedback Loop Workflow

1. **Data Collection**: Every query logged to `logs/feedback.jsonl` with:
   - Query, answer, citations
   - System confidence
   - User feedback (helpful/not helpful)

2. **Label Generation**: Feedback scores convert to NDCG labels:
   ```
   NDCG = helpful × confidence × (not_refused)
   ```

3. **Model Retraining**: Trigger periodically (daily/weekly):
   ```bash
   python training/train_ranker.py
   ```
   - Loads feedback logs
   - Generates training data (X, y, group_sizes)
   - Trains LambdaRank model
   - Saves with timestamp

4. **Model Versioning**: All models saved in `models/`:
   ```
   models/
   ├── ranker_20240101_120000.pkl  (v1)
   ├── ranker_20240102_030000.pkl  (v2, better)
   ├── training_log.jsonl
   ```

5. **Rollback**: If new model worse than baseline:
   ```python
   from app.ranking.model import LambdaRankModel
   
   # Load previous version
   model = LambdaRankModel()
   model.load("models/ranker_20240101_120000.pkl")
   ```

### Monitoring Training Quality

Check training logs after each run:
```bash
tail -5 models/training_log.jsonl | jq .
```

Expected output:
```json
{
  "timestamp": "2024-01-02T03:00:00",
  "n_samples": 342,
  "n_groups": 78,
  "features_mean": [0.76, 0.68, 0.45, 0.32, 0.88, 0.62],
  "labels_mean": 0.54,
  "labels_std": 0.31
}
```

---

## Production Checklist

### Before Deployment

- [ ] **Secrets Management**: Use environment variables for API keys
  ```bash
  export OPENAI_API_KEY="sk-..."
  ```

- [ ] **Data Validation**: Validate all input documents
  ```python
  from app.data import DataValidator
  validator = DataValidator()
  validator.validate_structured_data(docs)
  ```

- [ ] **Model Versioning**: Track model performance over time
  ```bash
  git tag -a v1.0-model-production -m "Production ranking model"
  ```

- [ ] **Monitoring Setup**: Enable metric collection
  ```python
  from app.monitoring import MetricsCollector
  metrics = MetricsCollector()
  ```

### During Operations

- [ ] **Daily Health Checks**:
  ```bash
  curl http://api:8000/health
  ```

- [ ] **Weekly Feedback Review**:
  ```bash
  curl http://api:8000/feedback/stats | jq .
  ```

- [ ] **Monthly Retraining**:
  ```bash
  python training/train_ranker.py
  ```

- [ ] **Quarterly Evaluation**: Full test suite on production data
  ```bash
  pytest tests/ -v --cov=app
  ```

---

## Troubleshooting

### Issue: High Refusal Rate (> 15%)

**Symptoms**: `/feedback/stats` shows `refused_rate` > 0.15

**Causes**:
- Query contains information not in documents
- Ranking confidence threshold too high (default: 0.5)

**Fix**:
```python
# Lower threshold temporarily
from app.llm.constrained import ConstrainedReasoning
reasoning = ConstrainedReasoning(confidence_threshold=0.4)
```

### Issue: Slow Latency (> 1s)

**Symptoms**: `/metrics` shows P95 latency > 1000ms

**Causes**:
- Dense retrieval slow on large dataset
- FAISS index not optimized

**Fix**:
```bash
# Rebuild FAISS index with IVF
python -c "
from app.retrieval.dense_retrieval import DenseRetriever
r = DenseRetriever(docs)
r.index = r.index.to_cpu()  # or GPU with faiss-gpu
"
```

### Issue: Recall Drop (< 65%)

**Symptoms**: `/metrics` shows retrieval_recall_mean < 0.65

**Causes**:
- Documents not relevant to queries
- Embedding model misaligned with domain

**Fix**:
1. Audit documents:
   ```bash
   python -c "
   from app.ingestion import load_docs
   docs = load_docs('data/unstructured/internal_docs.md')
   print(f'Loaded {len(docs)} documents')
   for doc in docs[:5]:
       print(f'  - {doc[:80]}...')
   "
   ```

2. Fine-tune embedding model on domain-specific data (advanced)

---

## Configuration

All settings in `app/config.py`:

```python
# Retrieval
TOP_K = 5                              # Top-K candidates to rank
DENSE_MODEL = "all-MiniLM-L6-v2"      # Sentence transformer model
DOC_PATH = "data/unstructured/internal_docs.md"

# Ranking
CONFIDENCE_THRESHOLD = 0.5             # LLM refusal threshold
MAX_TOKENS = 256                       # Answer length limit

# Monitoring
LATENCY_BASELINE = 300                 # P95 baseline (ms)
RECALL_BASELINE = 0.75                 # Recall baseline
REFUSAL_BASELINE = 0.08                # Refusal rate baseline

# Training
MIN_FEEDBACK_FOR_TRAINING = 50         # Minimum samples before retraining
TRAINING_EPOCHS = 100                  # LambdaRank training epochs
```

---

## Advanced: Custom Document Loader

To use custom data sources (databases, APIs), implement:

```python
from app.data import DataLoader

class CustomDataLoader(DataLoader):
    def load_documents(self, source):
        # Fetch from database/API
        docs = fetch_from_my_database()
        return [d.text for d in docs]

loader = CustomDataLoader()
docs = loader.load_documents("my_database")
```

---

## Support & Debugging

**View system logs**:
```bash
tail -100 logs/feedback.jsonl | jq .
tail -50 logs/metrics.jsonl | jq .
```

**Test a query end-to-end**:
```python
from app.pipeline import run_pipeline

result = run_pipeline("Why did metrics change?")
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Latency: {result['latency_ms']:.0f}ms")
```

**Run pytest with verbose output**:
```bash
pytest tests/test_pipeline.py -vv -s
```

---

## Performance Benchmarks

Typical performance on CPU (Intel i7, 8GB RAM):

| Operation | Latency | Notes |
|-----------|---------|-------|
| Dense Embedding | 50-100ms | Per query |
| Sparse Retrieval | 10-20ms | BM25 |
| Hybrid Merge | 5-10ms | Merging scores |
| Feature Extraction | 20-30ms | Per candidate (×5) |
| LambdaRank Inference | 10-15ms | Model prediction |
| LLM Synthesis | 100-200ms | Placeholder (w/ real LLM: 500-2000ms) |
| **Total** | **200-400ms** | End-to-end |

To optimize:
- Use FAISS GPU for dense search (50→10ms)
- Cache model weights in memory
- Batch process multiple queries
- Use async/await for I/O-bound operations

---

## License & Attribution

See LICENSE file. Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [LightGBM](https://lightgbm.readthedocs.io/)
- [rank-bm25](https://github.com/dorianbrown/rank_bm25)

