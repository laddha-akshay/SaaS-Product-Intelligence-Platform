# Ranking Evaluation - Metrics & Testing

Documentation for evaluating the learning-to-rank (LambdaRank) model performance.

## Overview

The ranking layer uses **LightGBM with LambdaRank** to reorder retrieval candidates by usefulness.

**Key Metric:** NDCG (Normalized Discounted Cumulative Gain) @ position K

---

## What the Ranker Does

### Input

- Query: "Why did activation drop in March?"
- Candidates from retrieval: [doc1, doc2, doc3, doc4, doc5]
- Each with dense_score, sparse_score, metadata

### Processing

1. Extract 6 features for each candidate
2. Feed to LambdaRank model
3. Predict ranking score for each candidate
4. Reorder: highest score first

### Output

- Ranked list: [doc3, doc1, doc4, doc2, doc5]
- Top-K for LLM: [doc3, doc1, doc4]
- With relevance scores: [0.95, 0.89, 0.72]

---

## Ranking Features (6-Dimensional)

| Feature           | Type  | Purpose                | Range      |
| ----------------- | ----- | ---------------------- | ---------- |
| `dense_score`     | float | Embedding similarity   | [0, 1]     |
| `sparse_score`    | float | BM25 relevance         | [0, ~10]   |
| `doc_length`      | int   | Word count             | [0, 10000] |
| `term_overlap`    | float | Query term match %     | [0, 1]     |
| `recency_decay`   | float | Days since last update | [0.1, 1.0] |
| `feedback_signal` | float | User feedback score    | [0, 1]     |

---

## NDCG Metric Explained

NDCG measures ranking quality by penalizing relevant documents that appear late.

### Example Ranking

**Query:** "Why did activation drop?"

**Ground truth (relevance labels):**

- doc1: Relevant (rel=1) ← mentions March + onboarding redesign
- doc2: Slightly relevant (rel=0.5) ← mentions product changes
- doc3: Highly relevant (rel=2) ← directly explains March activation drop
- doc4: Not relevant (rel=0) ← unrelated to query
- doc5: Not relevant (rel=0) ← unrelated to query

**System ranking:**

- Rank 1: doc3 (rel=2) ✅ Good! Most relevant at top
- Rank 2: doc1 (rel=1) ✅ Good! Second most relevant
- Rank 3: doc2 (rel=0.5) ⚠️ OK, but could be better
- Rank 4: doc4 (rel=0) ❌ Bad! Irrelevant document
- Rank 5: doc5 (rel=0) ❌ Bad! Irrelevant document

**NDCG@3 Calculation:**

```
DCG@3 = rel(rank1)/log(1+1) + rel(rank2)/log(2+1) + rel(rank3)/log(3+1)
       = 2/1 + 1/1.585 + 0.5/2
       = 2.0 + 0.631 + 0.25
       = 2.881

IDCG@3 (ideal: sort by relevance, take top 3)
      = 2/1 + 1/1.585 + 0.5/2
      = 2.881 (same as DCG in this case - we got it right!)

NDCG@3 = DCG@3 / IDCG@3 = 2.881 / 2.881 = 1.0 (perfect!)
```

---

### What Good NDCG Looks Like

| NDCG@3    | Interpretation | Action                               |
| --------- | -------------- | ------------------------------------ |
| > 0.85    | Excellent      | ✅ Production ready                  |
| 0.75-0.85 | Good           | ✅ OK for production with monitoring |
| 0.65-0.75 | Fair           | ⚠️ Needs improvement                 |
| < 0.65    | Poor           | ❌ Needs retraining                  |

---

## Label Generation from Feedback

Users provide binary feedback (helpful/not helpful). This generates NDCG labels.

### Process

1. **User Query:** "Why did activation drop?"
2. **System Returns:** Top-3 ranked docs + answer
3. **User Feedback:** "Helpful: Yes" (or No)
4. **Label Generation:**

   ```
   helpful = 1 if user_feedback == "yes" else 0
   confidence = 0.76 (from answer confidence score)
   not_refused = 1 if refused == false else 0

   label = helpful × confidence × not_refused
         = 1 × 0.76 × 1
         = 0.76
   ```

5. **Ranking Model Update:** Next retraining uses this query + label

---

## Evaluation Baseline

Expected performance over 100 test queries:

| Metric                       | Target | How Measured                       |
| ---------------------------- | ------ | ---------------------------------- |
| NDCG@3                       | > 0.78 | Gold query set                     |
| NDCG@5                       | > 0.75 | Gold query set                     |
| Recall@5                     | > 0.82 | % of relevant docs in top 5        |
| MRR (Mean Reciprocal Rank)   | > 0.85 | 1 / position of first relevant doc |
| MAP (Mean Average Precision) | > 0.80 | Area under precision curve         |

---

## Drift Detection

Monitor ranking performance in production.

### Metrics to Track

```
Weekly NDCG@3 values:
Week 1:  0.780
Week 2:  0.778
Week 3:  0.775
Week 4:  0.772  ← Trending down
Week 5:  0.768  ← Below threshold (0.75)
Week 6:  0.765  ← ALERT! Drift detected
```

### Baseline Thresholds

| Metric                     | Alert If | Action                  |
| -------------------------- | -------- | ----------------------- |
| NDCG@3 drops below         | 0.72     | Investigate + retrain   |
| Recall@5 drops below       | 0.75     | Check retrieval quality |
| MRR drops below            | 0.80     | Review ranking model    |
| Variance in NDCG increases | > 0.1    | Analyze by query type   |

---

## How to Evaluate Ranking

### Manual Evaluation (Gold Queries)

For each query, manually score: is the ranking good?

```bash
python -c "
from app.ranking.ranker import LambdaRankModel
from app.retrieval.hybrid_retrieval import HybridRetrieval

# Get retrieval results
hybrid = HybridRetrieval()
candidates = hybrid.search('Why did activation drop in March?')

# Rank them
ranker = LambdaRankModel()
ranked = ranker.rank_candidates('Why did activation drop in March?', candidates, top_k=5)

# Check: is most relevant doc first?
print(ranked)
"
```

### Automated Evaluation

```bash
# Run ranking evaluation on gold queries
python training/evaluate.py --metric ndcg --top_k 3

# Output:
# Query 1: NDCG@3 = 0.95
# Query 2: NDCG@3 = 0.82
# Query 3: NDCG@3 = 0.88
# ...
# Mean NDCG@3 = 0.878 ✅ PASS (> 0.78)
```

### Feedback-Based Evaluation

Track how users rate ranked results.

```bash
# Check feedback stats
curl http://localhost:8000/feedback/stats

# Output:
# {
#   "total_interactions": 156,
#   "helpful_rate": 0.81,      ← 81% of answers were helpful
#   "feedback_rate": 0.45,     ← 45% users gave feedback
#   "refused_rate": 0.12,      ← 12% were refused
#   "avg_confidence": 0.73
# }
```

**Interpretation:**

- helpful_rate 0.81 → Ranking is working! Users find answers helpful.
- feedback_rate 0.45 → Could improve feedback collection.

---

## Retraining the Ranker

Feedback drives ranking improvements.

### Step 1: Generate Training Data

```bash
# Extract NDCG labels from feedback logs
python training/prepare_training_data.py

# Output:
# Loaded 156 interactions
# Generated 120 NDCG labels (77% feedback coverage)
# Training data saved to models/training_data.pkl
```

### Step 2: Train New Model

```bash
# Retrain on feedback-generated labels
python training/train_ranker.py --epochs 100 --output_dir models

# Output:
# Training on 120 samples with 6 features
# Epoch 1/100: Loss = 0.892, NDCG@3 = 0.76
# Epoch 2/100: Loss = 0.854, NDCG@3 = 0.79
# ...
# Epoch 100/100: Loss = 0.521, NDCG@3 = 0.842
# Model saved: models/ranker_20260217_001500.pkl
```

### Step 3: Validate

```bash
# Evaluate on gold queries
python training/evaluate.py --model models/ranker_20260217_001500.pkl

# Output:
# Mean NDCG@3 = 0.882
# Improvement: +0.004 from previous
# Status: ✅ READY FOR DEPLOYMENT
```

### Step 4: Deploy

```bash
# Update production model (soft switch, no downtime)
cp models/ranker_20260217_001500.pkl models/ranker_production.pkl

# Canary: 10% traffic to new model
# Monitor: Error rates, latency, NDCG
# If good after 24h: 100% traffic to new model
```

---

## Common Ranking Issues & Fixes

| Issue          | Symptom                   | Root Cause              | Fix                            |
| -------------- | ------------------------- | ----------------------- | ------------------------------ |
| NDCG too low   | < 0.72                    | Poor features or labels | Retrain with more feedback     |
| High variance  | NDCG varies 0.6-0.9       | Inconsistent labels     | Review label generation logic  |
| Overfitting    | Train NDCG high, test low | Model too complex       | Regularization, early stopping |
| No improvement | NDCG stuck at 0.75        | Insufficient feedback   | Increase feedback collection   |
| Rank inversion | Bad docs ranked first     | Feature quality issues  | Improve dense/sparse retrieval |

---

## Best Practices

1. **Always track NDCG@3 and NDCG@5**: Top-3 matters most for users.
2. **Validate before deployment**: Must pass gold query test.
3. **Monitor in production**: Weekly NDCG checks for drift.
4. **Collect feedback**: Every interaction improves ranking.
5. **Retrain monthly**: Fresh data keeps model sharp.
6. **Keep baseline model**: Rollback if new model fails.
7. **A/B test if possible**: Compare old vs new model on users.

---

## References

- **NDCG Explained**: https://en.wikipedia.org/wiki/Discounted_cumulative_gain
- **LambdaRank Paper**: "From RankNet to LambdaRank to LambdaMART: An Overview" by Burges (2010)
- **LightGBM Ranking**: https://lightgbm.readthedocs.io/en/latest/Experiments.html#lambdank
