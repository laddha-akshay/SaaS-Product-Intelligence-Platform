# Retrieval Evaluation - Metrics & Testing

Documentation for evaluating the hybrid retrieval (dense + sparse) performance.

## Overview

The retrieval layer combines:

- **Dense Retrieval:** SentenceTransformers embeddings + FAISS vector search
- **Sparse Retrieval:** BM25 keyword-based search

**Key Metric:** Recall (Did we get the right documents?)

---

## What the Retriever Does

### Input

- Query: "Why did activation drop in March?"
- Document corpus: 50 internal documents

### Processing

#### Dense Retrieval

1. Embed query to 384-dim vector
2. FAISS searches for K=10 nearest neighbors by cosine similarity
3. Returns: [doc1, doc3, doc5, ...] with similarity scores

#### Sparse Retrieval

1. Tokenize query: ["why", "activation", "drop", "march"]
2. BM25 scores each document against these tokens
3. Returns: [doc2, doc1, doc4, ...] with BM25 scores

#### Hybrid Merge

1. Normalize scores (dense: [0,1], sparse: [0,1])
2. Combine: combined_score = 0.5 × dense_norm + 0.5 × sparse_norm
3. Rerank by combined score
4. Return top-K candidates: [doc1, doc3, doc2, ...]

### Output

- Top-5 candidate documents (before ranking)
- With scores and metadata
- Ready for ranking layer

---

## Retrieval Metrics

### 1. Recall@K

Percentage of relevant documents found in top-K results.

**Formula:**

```
Recall@K = (# relevant docs in top-K) / (# total relevant docs)
```

**Example:**

Query: "Why did activation drop in March?"

Relevant documents (from gold standard):

- doc3 ✅ "March onboarding redesign"
- doc8 ✅ "Release 2.3 activation impact"
- doc15 ✅ "User signup flow changes"
- doc22 ✅ "Q1 metrics analysis"

System returns top-5:

- Rank 1: doc3 ✅ RELEVANT
- Rank 2: doc8 ✅ RELEVANT
- Rank 3: doc2 ❌ not relevant
- Rank 4: doc15 ✅ RELEVANT
- Rank 5: doc7 ❌ not relevant

```
Recall@5 = 3 / 4 = 0.75 (75%)
```

### 2. Precision@K

Percentage of retrieved documents that are relevant.

**Formula:**

```
Precision@K = (# relevant docs in top-K) / K
```

**Using same example:**

```
Precision@5 = 3 / 5 = 0.60 (60%)
```

**Interpretation:**

- High recall, lower precision = getting all docs but with noise
- This is OK for retrieval; ranking will filter noise

### 3. Mean Reciprocal Rank (MRR)

Position of first relevant document.

**Formula:**

```
MRR = 1 / (position of first relevant doc)
```

**Example:**

- If first relevant doc at rank 1: MRR = 1/1 = 1.0 (perfect)
- If first relevant doc at rank 2: MRR = 1/2 = 0.5
- If first relevant doc at rank 5: MRR = 1/5 = 0.2
- If no relevant doc found: MRR = 0

Using example above (first relevant at rank 1):

```
MRR = 1.0
```

### 4. F1 Score (Harmonic Mean)

Balances recall and precision.

**Formula:**

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

Using example:

```
F1 = 2 × (0.60 × 0.75) / (0.60 + 0.75)
   = 2 × 0.45 / 1.35
   = 0.67
```

---

## Retrieval Baselines

Expected performance over 100 gold queries:

| Metric      | Dense Only | Sparse Only | Hybrid   | Target |
| ----------- | ---------- | ----------- | -------- | ------ |
| Recall@5    | 0.78       | 0.72        | **0.85** | > 0.82 |
| Recall@10   | 0.88       | 0.81        | **0.92** | > 0.90 |
| Precision@5 | 0.72       | 0.68        | **0.78** | > 0.75 |
| MRR         | 0.82       | 0.75        | **0.88** | > 0.85 |
| F1@5        | 0.75       | 0.70        | **0.81** | > 0.78 |

**Key Insight:** Hybrid retrieval outperforms both dense and sparse alone.

---

## Drift Detection

Monitor retrieval quality in production.

### Metrics to Track Weekly

```
Week 1 Recall@5:  0.845
Week 2 Recall@5:  0.843
Week 3 Recall@5:  0.840
Week 4 Recall@5:  0.835
Week 5 Recall@5:  0.828  ← Below threshold (0.82)
Week 6 Recall@5:  0.820  ← ALERT!
```

### Baseline Thresholds

| Metric                | Alert If | Severity | Action                   |
| --------------------- | -------- | -------- | ------------------------ |
| Recall@5 < 0.80       | Yes      | High     | Investigate + retrain    |
| Recall@10 < 0.88      | Yes      | Medium   | Monitor closely          |
| Precision@5 < 0.72    | Yes      | Low      | Check retrieval weights  |
| MRR < 0.82            | Yes      | Medium   | Review embedding quality |
| Dense avg score drops | > 10%    | High     | Check embeddings update  |
| BM25 score drops      | > 10%    | Low      | Check document indexing  |

---

## How to Evaluate Retrieval

### 1. Manual Evaluation

For key queries, manually check: are relevant docs in top-5?

```bash
python -c "
from app.retrieval.hybrid_retrieval import HybridRetrieval

hybrid = HybridRetrieval()

# Test a query
query = 'Why did activation drop in March?'
results = hybrid.search(query, top_k=5)

for i, (doc, score) in enumerate(results, 1):
    print(f'{i}. Doc: {doc[:50]}... (score: {score:.3f})')

# Manual check: Are the relevant docs here?
"
```

### 2. Automated Evaluation (Gold Queries)

```bash
# Evaluate on gold query set
python -c "
from app.retrieval.hybrid_retrieval import HybridRetrieval
import json

# Load gold queries (with known relevant docs)
with open('tests/gold_queries.md') as f:
    # Parse gold queries...
    pass

hybrid = HybridRetrieval()

metrics = {'recall_5': [], 'precision_5': [], 'mrr': []}

for query, relevant_docs in gold_queries:
    results = hybrid.search(query, top_k=5)
    retrieved_docs = [doc for doc, _ in results]

    # Calculate metrics
    recall = len(set(retrieved_docs) & set(relevant_docs)) / len(relevant_docs)
    precision = len(set(retrieved_docs) & set(relevant_docs)) / len(retrieved_docs)
    mrr = 1.0 / (next((i for i, d in enumerate(retrieved_docs, 1) if d in relevant_docs), float('inf')))

    metrics['recall_5'].append(recall)
    metrics['precision_5'].append(precision)
    metrics['mrr'].append(mrr)

print(f'Mean Recall@5: {sum(metrics[\"recall_5\"]) / len(metrics[\"recall_5\"]):.3f}')
print(f'Mean Precision@5: {sum(metrics[\"precision_5\"]) / len(metrics[\"precision_5\"]):.3f}')
print(f'Mean MRR: {sum(metrics[\"mrr\"]) / len(metrics[\"mrr\"]):.3f}')
"
```

### 3. Dense vs Sparse Comparison

See which retrieval method is helping:

```bash
python -c "
from app.retrieval.dense_retrieval import DenseRetrieval
from app.retrieval.sparse_retrieval import SparseRetrieval

query = 'Why did activation drop in March?'

dense = DenseRetrieval()
sparse = SparseRetrieval()

dense_results = dense.search(query, top_k=5)
sparse_results = sparse.search(query, top_k=5)

print('DENSE RETRIEVAL:')
for i, (doc, score) in enumerate(dense_results, 1):
    print(f'  {i}. Score={score:.3f} Doc={doc[:40]}...')

print('\nSPARSE RETRIEVAL:')
for i, (doc, score) in enumerate(sparse_results, 1):
    print(f'  {i}. Score={score:.3f} Doc={doc[:40]}...')

print('\nAnalysis:')
print('Which docs only dense finds? (semantic matches)')
print('Which docs only sparse finds? (keyword matches)')
print('Which docs both find? (strong matches)')
"
```

---

## Common Retrieval Issues & Fixes

| Issue                  | Symptom                         | Cause                         | Fix                                |
| ---------------------- | ------------------------------- | ----------------------------- | ---------------------------------- |
| Low Recall             | < 0.80                          | Missing relevant docs         | Increase top-K, improve embeddings |
| Dense underperforms    | FAISS finds wrong docs          | Bad embeddings or OOD queries | Retrain embeddings on domain data  |
| Sparse underperforms   | BM25 misses documents           | Bad tokenization/indexing     | Check stopwords, reindex docs      |
| Hybrid not helping     | Same as individual methods      | Poor weight balance (0.5/0.5) | Try 0.6/0.4 or 0.4/0.6             |
| Latency creep          | Retrieval > 100ms               | FAISS index growing           | Reduce top-K before ranking        |
| Score distribution off | All scores clustered [0.1, 0.2] | Normalization issue           | Check score scaling                |

---

## Optimization Opportunities

### 1. Improve Dense Embeddings

**Current:** all-MiniLM-L6-v2 (general purpose)

**Alternatives:**

- Fine-tune on your domain data → Domain-specific embeddings
- Use larger model → Better quality but slower
- Distill model → Smaller, faster

### 2. Improve Sparse Search

**Current:** BM25Okapi with default tokenization

**Optimizations:**

- Custom tokenization (keep domain terms)
- Remove less important stopwords
- Add stemming/lemmatization
- Query expansion (related terms)

### 3. Better Weighting

**Current:** 50% dense + 50% sparse

**Test alternatives:**

```
80% dense + 20% sparse → semantic-heavy
30% dense + 70% sparse → keyword-heavy
Adaptive: varies by query type
```

### 4. Reranking

Add intermediate ranking step:

```
Retrieval (top-100) → Lightweight ranker (top-20) → Expensive ranker (top-5)
```

---

## Retrieval Benchmarking

### Setup

```bash
# Create benchmark queries (100 queries, known relevant docs)
python -c "
import json
from tests.gold_queries import GOLD_QUERIES

benchmark = {
    'queries': [q['query'] for q in GOLD_QUERIES],
    'relevant_docs': [q['expected_docs'] for q in GOLD_QUERIES]
}

with open('benchmarks/retrieval_benchmark.json', 'w') as f:
    json.dump(benchmark, f)
"
```

### Run Benchmark

```bash
python -c "
import json
import time
from app.retrieval.hybrid_retrieval import HybridRetrieval

with open('benchmarks/retrieval_benchmark.json') as f:
    benchmark = json.load(f)

hybrid = HybridRetrieval()
results = {
    'recall_5': [],
    'precision_5': [],
    'latency_ms': []
}

for query, relevant_docs in zip(benchmark['queries'], benchmark['relevant_docs']):
    start = time.time()
    retrieved = hybrid.search(query, top_k=5)
    latency = (time.time() - start) * 1000

    retrieved_docs = [doc for doc, _ in retrieved]
    recall = len(set(retrieved_docs) & set(relevant_docs)) / len(relevant_docs)
    precision = len(set(retrieved_docs) & set(relevant_docs)) / 5

    results['recall_5'].append(recall)
    results['precision_5'].append(precision)
    results['latency_ms'].append(latency)

print(f'Recall@5: {sum(results[\"recall_5\"]) / len(results[\"recall_5\"]):.3f}')
print(f'Precision@5: {sum(results[\"precision_5\"]) / len(results[\"precision_5\"]):.3f}')
print(f'Mean Latency: {sum(results[\"latency_ms\"]) / len(results[\"latency_ms\"]):.1f}ms')
print(f'P95 Latency: {sorted(results[\"latency_ms\"])[int(0.95*len(results[\"latency_ms\"]))]:.1f}ms')
"
```

---

## Best Practices

1. **Always monitor Recall@5 and Recall@10**: These matter most for downstream ranking.
2. **Track latency**: Retrieval should be < 100ms P95.
3. **Compare dense vs sparse**: Understand what each retrieval method contributes.
4. **Test weight balance**: 50/50 isn't always optimal; try 40/60 or 60/40.
5. **Check for drift**: Weekly metrics to catch index degradation.
6. **Use gold queries**: Validate on known-good test set before deployment.
7. **Profile latency**: Dense embedding + FAISS is usually fast. Sparse scales with corpus.

---

## References

- **Recall & Precision:** https://en.wikipedia.org/wiki/Precision_and_recall
- **MRR & NDCG:** https://en.wikipedia.org/wiki/Mean_reciprocal_rank
- **BM25:** https://en.wikipedia.org/wiki/Okapi_BM25
- **FAISS:** https://github.com/facebookresearch/faiss
- **Hybrid Search:** https://docs.pinecone.io/docs/hybrid-search
