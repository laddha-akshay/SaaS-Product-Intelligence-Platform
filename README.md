# SaaS Product Intelligence Platform

A production-style machine learning system that helps SaaS teams understand **why product metrics change** by combining hybrid retrieval, learning-to-rank, and constrained reasoning.

This project demonstrates end-to-end ML system design including ingestion, retrieval, ranking, reasoning, feedback, evaluation, and deployment.

---

## Overview

Modern SaaS companies generate large volumes of structured and unstructured data such as:

- Product usage events
- Business metrics
- Support tickets
- Release notes
- Internal documentation

Dashboards explain _what happened_ but rarely explain _why_.  
Traditional LLM systems can generate explanations but often hallucinate or rely on incomplete context.

This platform addresses that gap by producing **grounded, explainable insights** backed by evidence.

---

## Key Features

- Hybrid retrieval (dense semantic + sparse keyword search)
- Learning-to-Rank model (LambdaRank) for usefulness optimization
- Evidence-constrained reasoning layer with citations and confidence
- Feedback-driven improvement pipeline
- Offline evaluation and experiment tracking (MLflow)
- Dockerized deployment
- FastAPI inference service

---

## System Architecture

End-to-end pipeline:

1. Data ingestion and validation
2. Hybrid retrieval to maximize recall
3. Learning-to-Rank model to reorder by usefulness
4. Constrained reasoning layer operating only on ranked evidence
5. Feedback collection and retraining
6. Monitoring and rollback support

The reasoning layer is treated as a **reasoning component**, not a source of truth.

---

## Repository Structure

```
saas_product_intelligence_platform/
│
├── app/
│   ├── api.py
│   ├── config.py
│   ├── ingestion.py
│   ├── dense_retrieval.py
│   ├── sparse_retrieval.py
│   ├── hybrid_retrieval.py
│   ├── ranker.py
│   ├── llm.py
│   └── pipeline.py
│
├── training/
│   ├── train_ranker.py
│   └── evaluate.py
│
├── data/
│   ├── structured/
│   └── unstructured/
│
├── experiments/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.py
```

---

## Installation

### Local setup

```bash
git clone https://github.com/laddha-akshay/SaaS-Product-Intelligence-Platform.git
cd SaaS-Product-Intelligence-Platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Start Demo

See the system in action with just one command:

```bash
python demo.py
```

This runs 3 sample queries demonstrating:

- Hybrid retrieval (dense semantic + sparse keyword search)
- Learning-to-Rank model reordering candidates by usefulness
- Constrained reasoning layer generating evidence-based answers
- Citations pulled directly from source documents
- Confidence scores and latency metrics

**Example Output:**

```
📋 QUERY: Why did activation drop in January?

📊 ANSWER:
Based on internal documentation: - Activation dropped 18% in first 48h (from 42% to 34%)...

🔗 CITATIONS:
   [1] - Activation dropped 18% in first 48h (from 42% to 34%)
   [2] - Mar 1: v1 marked deprecated (still works, warnings in logs)

📈 METRICS:
   • Confidence: 60.81%
   • Latency: 1.89ms
```

---

## Running the API

Start the FastAPI inference service:

```bash
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Make queries via HTTP:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Why did activation drop?"}'
```

---

### Docker setup

```bash
docker-compose up --build
```

---

## Training the Ranking Model

```bash
python training/train_ranker.py
```

Evaluate:

```bash
python training/evaluate.py
```

MLflow experiment results are stored under the `experiments/` directory.

---

## Example API Call

POST request:

```
POST /query
```

Body:

```json
{
  "query": "Why did activation drop last week?"
}
```

Response:

```json
{
  "answer": "...",
  "citations": [...],
  "confidence": 0.78
}
```

---

## Testing and Evaluation

The system is validated across multiple layers:

- Data integrity validation
- Retrieval Recall@K evaluation
- Ranking NDCG and Precision@K
- LLM grounding and refusal tests
- End-to-end usefulness evaluation
- Latency and reliability tracking

Regression tests ensure model or prompt changes do not degrade performance.

---

## Design Principles

- Optimize systems rather than individual models
- Treat retrieval and ranking as first-class ML components
- Favor refusal over hallucinated answers
- Build feedback-driven continuous learning loops
- Prioritize observability and rollback

---

## Future Improvements

- Multi-tenant deployment
- Active learning for ranking labels
- Cost-aware routing across LLM providers
- Real-time feature store integration
- Monitoring dashboards

---

## What This Project Demonstrates

- End-to-end ML system design
- Hybrid retrieval and ranking pipelines
- Production-ready inference service
- Experiment tracking and evaluation workflows
- Reliable, explainable AI system design

---

## License

MIT License
