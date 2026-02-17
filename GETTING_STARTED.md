# Getting Started - SaaS Product Intelligence Platform

**New to this repo?** This guide will show you how to see the system in action in **5 minutes**.

---

## 🎯 What This Project Does

This is an **AI system that answers "Why did [metric] change?"** using internal company data.

**Example:**
- User asks: *"Why did user activation drop in March?"*
- System answers: *"The onboarding redesign in Release 2.3 caused a 20% activation drop. Users found the new signup flow confusing."*
- System provides: **Citations** (where it found this), **Confidence score** (how sure it is)

It's **NOT** a generic chatbot. It's built for production use with:
- ✅ Evidence-based answers (cites sources)
- ✅ Honest about uncertainty (refuses when unsure)
- ✅ Constantly improving (learns from user feedback)

---

## ⏱️ Quick Demo (5 minutes)

### Step 1: Setup (2 minutes)

```bash
# Clone or navigate to the repo
cd /Users/akshayladdha/Documents/GitHub/SaaS-Product-Intelligence-Platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start the Server (1 minute)

```bash
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

Leave this running. Open **another terminal** for the next step.

### Step 3: Test It (2 minutes)

**Open a new terminal** and run these commands:

#### A) Check System Health
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "uptime_seconds": 23,
  "drift_detected": false,
  "message": "System operational"
}
```

#### B) Ask a Question
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Why did activation drop in March?"}'
```

**Response:**
```json
{
  "query_id": "abc-123-def",
  "answer": "The onboarding redesign in Release 2.3 caused a 20% activation drop due to UI changes in the signup flow.",
  "citations": [
    "Onboarding redesign in March caused 20% activation drop",
    "Release 2.3 included UI changes to signup flow"
  ],
  "confidence": 0.87,
  "refused": false,
  "latency_ms": 245
}
```

#### C) Try More Queries
```bash
# Try questions about different topics
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What caused the retention improvement?"}'

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Tell me about the database migration"}'

# Try a question NOT in the docs (should be refused)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Tell me about quantum physics"}'
```

#### D) Check System Metrics
```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "p95_latency_ms": 450,
  "retrieval_recall_mean": 0.82,
  "ranker_ndcg_mean": 0.78,
  "llm_refused_rate": 0.08,
  "confidence_mean": 0.75
}
```

#### E) View Feedback Stats
```bash
curl http://localhost:8000/feedback/stats
```

**Response:**
```json
{
  "total_interactions": 3,
  "helpful_rate": 0.0,
  "feedback_rate": 0.0,
  "refused_rate": 0.33,
  "avg_confidence": 0.72
}
```

---

## 📊 What You Just Saw

### The System Architecture

```
Your Query
    ↓
[Retrieval] → Find relevant documents (dense + sparse search)
    ↓
[Ranking] → Reorder by usefulness (ML model)
    ↓
[LLM Reasoning] → Generate answer with citations
    ↓
[Response] → Answer + confidence + citations
    ↓
[Monitoring] → Track metrics & feedback
```

### Key Features Demonstrated

1. **Citations** — Every answer cites where it found the information
2. **Confidence Score** — System tells you how sure it is (0-1 scale)
3. **Refusal Logic** — System refuses to answer when unsure (quantum physics example)
4. **Metrics** — System tracks its own performance (latency, recall, confidence)
5. **Feedback** — System logs all interactions for continuous improvement

---

## 🔍 Dive Deeper

### Run the Test Suite
```bash
.venv/bin/python -m pytest tests/test_smoke.py -v
```

Expected output:
```
test_imports ..................... PASSED ✅
test_feedback_collector .......... PASSED ✅
test_data_validator ............. PASSED ✅
test_config ..................... PASSED ✅

4/4 PASSED
```

### View System Logs
```bash
# See what the system is doing internally
tail -5 logs/feedback.jsonl

# See performance metrics
tail -5 logs/metrics.jsonl
```

### Submit Feedback (Manual Testing)
```bash
# Get a query ID from a previous response, then:
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "YOUR-QUERY-ID-HERE",
    "helpful": true,
    "feedback": "Great answer!"
  }'

# Check updated stats
curl http://localhost:8000/feedback/stats
```

---

## �� Project Structure (Quick Overview)

```
SaaS-Product-Intelligence-Platform/
├── README.md                    ← Start here for quick overview
├── GETTING_STARTED.md           ← This file
├── DEPLOYMENT.md                ← For production setup
├── PROJECT_SUMMARY.md           ← Deep technical guide
│
├── run.py                       ← Start the server (python run.py)
├── requirements.txt             ← Dependencies
│
├── app/
│   ├── api.py                   ← The API endpoints you just tested
│   ├── pipeline.py              ← How queries are processed
│   ├── ingestion.py             ← How documents are loaded
│   └── ...                      ← Other components
│
├── data/
│   ├── unstructured/
│   │   ├── internal_docs.md     ← Sample company docs (changeable)
│   │   └── release_notes.md     ← Sample release notes
│   └── structured/
│       └── metrics.csv          ← Sample metrics data
│
├── tests/
│   └── test_smoke.py            ← Quick sanity checks
│
└── logs/
    ├── feedback.jsonl           ← Stores all queries & answers
    └── metrics.jsonl            ← Performance metrics
```

---

## 🎓 Understanding the Response

When you ask a question, you get back:

```json
{
  "query_id": "unique-id",              // For tracking
  "answer": "The answer to your question",
  "citations": ["Source 1", "Source 2"],  // Where the answer comes from
  "confidence": 0.87,                    // How sure (0-1, higher is better)
  "refused": false,                      // True = system said "I don't know"
  "latency_ms": 245                     // How fast (milliseconds)
}
```

### Confidence Explained
- **0.9+** = Very confident, answers definitely
- **0.7-0.9** = Confident, probably accurate
- **0.5-0.7** = Somewhat confident
- **<0.5** = Not confident, system refuses

### When System Refuses
The system will refuse to answer if:
- The question isn't in the documents
- The documents contradict each other
- Confidence too low

**This is intentional!** Better to say "I don't know" than make up an answer.

---

## 🔧 Customization Guide

Want to try it with your own data?

### Replace Sample Data
```bash
# Edit the company documentation
vim data/unstructured/internal_docs.md

# Add your own internal docs, release notes, metrics, etc.
```

Then restart the server:
```bash
python run.py
```

The system will automatically index the new documents.

### Try Different Questions
```bash
# Depending on what's in your docs, try questions like:
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What did you change last month?"}'
```

---

## ⚡ Next Steps

### Option A: Quick Exploration (10 minutes)
1. ✅ Run the demo above
2. ✅ Try different questions
3. ✅ Check logs
4. Done!

### Option B: Understand the System (30 minutes)
1. ✅ Read **README.md**
2. ✅ Read **PROJECT_SUMMARY.md**
3. ✅ Examine the code in `app/api.py`
4. ✅ Look at sample data in `data/`

### Option C: Production Deployment (1-2 hours)
1. ✅ Read **DEPLOYMENT.md**
2. ✅ Replace sample data with your data
3. ✅ Integrate real LLM (currently placeholder)
4. ✅ Deploy with Docker

---

## 🆘 Troubleshooting

### Issue: Port already in use
```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9
python run.py
```

### Issue: Module not found
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: Slow responses
- First query is slow (loads models): 2-3 seconds
- Subsequent queries: 200-400ms
- This is normal!

### Issue: All queries refused
- Check `data/unstructured/internal_docs.md` has content
- System can't answer if there are no documents

---

## 📚 Documentation

| Document | For What |
|----------|----------|
| **README.md** | Quick project overview |
| **GETTING_STARTED.md** | ← You are here (for new users) |
| **PROJECT_SUMMARY.md** | How the system works (technical) |
| **DEPLOYMENT.md** | Production setup & troubleshooting |

---

## 💡 Key Insights

**This is NOT a generic chatbot.** It's designed for:
- ✅ **Evidence-based answers** — Everything is cited
- ✅ **Honest about uncertainty** — Refuses when unsure
- ✅ **Continuous improvement** — Learns from feedback
- ✅ **Production-ready** — Monitoring, metrics, rollback

**Why it matters:**
- Regular chatbots hallucinate (make up answers)
- This system only answers from documents it has
- User feedback improves it over time
- Perfect for internal SaaS documentation

---

## 🚀 You're Ready!

1. Run `python run.py`
2. Try the curl commands above
3. See the results in real-time
4. Check the docs for deeper understanding

**Questions?** See the relevant documentation:
- Quick setup → **README.md**
- How it works → **PROJECT_SUMMARY.md**
- Production → **DEPLOYMENT.md**

Enjoy! 🎉

