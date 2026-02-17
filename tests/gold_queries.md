# Gold Queries - Test Cases

Gold standard queries for evaluating retrieval, ranking, and LLM reasoning quality.
These are queries with known, expected answers from the system's document corpus.

## Category 1: Product & Feature Questions

### Query 1: Activation Drop

**Query:** "Why did user activation drop in March?"

**Expected Answer Structure:**

- Main cause: Onboarding redesign (Release 2.3)
- Impact: 20% activation drop
- Root reason: UI changes in signup flow confuse users
- Timeline: March 2024
- Source documents: release_notes.md, support_tickets.json

**Acceptance Criteria:**

- ✅ Mentions Release 2.3
- ✅ Cites onboarding changes
- ✅ Confidence > 0.7
- ✅ Includes at least 2 citations
- ✅ Latency < 500ms

---

### Query 2: Retention Improvement

**Query:** "What caused the retention improvement in Q4?"

**Expected Answer Structure:**

- Main cause: Retention features (feature flags, email campaigns)
- Impact: 15% improvement
- Timeline: Q4 2024
- Source: release_notes.md, internal_docs.md

**Acceptance Criteria:**

- ✅ Mentions feature flags or retention features
- ✅ Cites data from Q4
- ✅ Confidence > 0.65
- ✅ At least 2 citations
- ✅ Latency < 500ms

---

### Query 3: Database Performance

**Query:** "Tell me about the database migration and its impact"

**Expected Answer Structure:**

- Migration details: PostgreSQL upgrade from v12 to v14
- Impact: Improved query performance
- Timeline: January 2024
- Benefits: Reduced latency by 30%
- Source: internal_docs.md, release_notes.md

**Acceptance Criteria:**

- ✅ Mentions PostgreSQL versions
- ✅ Cites performance improvements
- ✅ Confidence > 0.7
- ✅ At least 1 citation
- ✅ Latency < 500ms

---

### Query 4: API Changes

**Query:** "What breaking changes were made in the latest API release?"

**Expected Answer Structure:**

- Breaking change: Deprecated v1 endpoints
- Replacement: v2 API with improved response format
- Timeline: February 2024
- Migration notes: Provided in docs
- Source: release_notes.md

**Acceptance Criteria:**

- ✅ Mentions API versioning
- ✅ Cites specific endpoints or changes
- ✅ Confidence > 0.65
- ✅ At least 1 citation
- ✅ Latency < 500ms

---

## Category 2: Refusal Test Cases

These queries should be **refused** (confidence < 0.5) because answers don't exist in documents.

### Query 5: Out of Scope Question

**Query:** "Tell me about quantum physics and its applications"

**Expected Behavior:**

- ✅ Refused: true
- ✅ Confidence < 0.5
- ✅ Message indicates lack of knowledge
- ✅ No hallucinated answer

---

### Query 6: No Relevant Documents

**Query:** "What is your CEO's favorite ice cream flavor?"

**Expected Behavior:**

- ✅ Refused: true
- ✅ Confidence < 0.5
- ✅ No citations
- ✅ Graceful refusal message

---

### Query 7: Future Events

**Query:** "What will be released in Q2 2026?"

**Expected Behavior:**

- ✅ Refused: true (not in documents)
- ✅ Confidence < 0.5
- ✅ System admits uncertainty about future

---

## Category 3: Edge Cases

### Query 8: Ambiguous Question

**Query:** "What changed?"

**Expected Behavior:**

- ✅ Either refuses (confidence < 0.5) or
- ✅ Asks for clarification in answer
- ✅ Does not hallucinate

---

### Query 9: Multi-part Question

**Query:** "What happened in March and how does it relate to Q4?"

**Expected Behavior:**

- ✅ Attempts to answer both parts
- ✅ Or refuses if insufficient data
- ✅ Confidence reflects uncertainty

---

### Query 10: Contradictory Query

**Query:** "Did activation go up or down in March?"

**Expected Behavior:**

- ✅ Clearly states: Activation went DOWN 20%
- ✅ Confidence > 0.7
- ✅ Cites sources

---

## Evaluation Metrics for Gold Queries

### Per-Query Metrics

| Metric                 | Target  | Description                                 |
| ---------------------- | ------- | ------------------------------------------- |
| Recall@5               | > 0.8   | At least 4 of top 5 docs are relevant       |
| NDCG@3                 | > 0.75  | Ranking quality (how much users like top 3) |
| Confidence Calibration | ±0.1    | System confidence matches actual accuracy   |
| Citation Coverage      | 100%    | Every claim is cited                        |
| Latency P95            | < 500ms | Response time                               |
| Refusal Accuracy       | 100%    | Correct refusals for OOD queries            |

### Aggregate Metrics

| Metric                               | Target    |
| ------------------------------------ | --------- |
| Accuracy (correct answers)           | > 85%     |
| Precision (no hallucinations)        | > 95%     |
| Recall (finds relevant info)         | > 80%     |
| Refusal Precision (correct refusals) | > 90%     |
| Mean Confidence                      | 0.70-0.80 |

---

## How to Use These Gold Queries

### For Manual Testing

```bash
# Run each query manually
python run.py

# Test in another terminal
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Why did user activation drop in March?"}'
```

### For Automated Evaluation

```bash
# Run evaluation script
python testing/evaluate_gold_queries.py --verbose

# Expected output:
# Query 1: PASS (accuracy: 0.92, latency: 245ms)
# Query 2: PASS (accuracy: 0.88, latency: 310ms)
# ...
# Summary: 10/10 PASS
```

### For Continuous Monitoring

Gold queries should be run weekly in production to detect:

- Degradation in retrieval quality
- Drift in ranking model
- Increase in hallucinations
- Changes in latency

---

## Notes

- All gold queries are based on the `data/` directory documents
- Update these queries when documents change
- Add new queries when discovering edge cases in production
- Use these for regression testing before deployments
