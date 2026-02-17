# LLM Integration Guide

This guide walks you through integrating a real LLM API (OpenAI, Anthropic, etc.) into the SaaS Product Intelligence Platform.

---

## 📋 Table of Contents

1. [Current State](#current-state)
2. [Why Integration?](#why-integration)
3. [OpenAI Integration (Recommended)](#openai-integration-recommended)
4. [Anthropic Integration](#anthropic-integration)
5. [Other Providers](#other-providers)
6. [Testing Your Integration](#testing-your-integration)
7. [Troubleshooting](#troubleshooting)

---

## Current State

The system currently uses a **deterministic, rule-based answer generator** that:
- ✅ Works without any API key
- ✅ Extracts answers from retrieved documents
- ✅ Computes confidence from retrieval quality
- ✅ Never hallucinates (always cites sources)

This is intentional for safety, but you can enhance it with a real LLM that generates more fluent, contextually aware answers.

---

## Why Integration?

| Aspect | Without LLM | With LLM |
|--------|------------|----------|
| Answer Generation | Extract from docs | Synthesize & rephrase |
| Fluency | Good | Excellent |
| Contextual Understanding | Basic | Advanced |
| Response Variety | Limited | Rich |
| Hallucination Risk | None | Low (with constraints) |

---

## OpenAI Integration (Recommended)

### Step 1: Get Your API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to **API keys** → **Create new secret key**
4. Copy and save the key (you won't see it again!)

### Step 2: Install Dependencies

```bash
pip install openai python-dotenv
```

Or update `requirements.txt`:

```txt
openai>=1.3.0
python-dotenv>=1.0.0
```

Then install:

```bash
pip install -r requirements.txt
```

### Step 3: Create `.env` File

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for cheaper
OPENAI_TEMPERATURE=0.3  # Lower = more deterministic
```

**⚠️ Important:** Add `.env` to `.gitignore` so your key never gets pushed to GitHub:

```bash
echo ".env" >> .gitignore
```

### Step 4: Update `app/config.py`

Add environment variable loading:

```python
"""Configuration constants."""
import os
from dotenv import load_dotenv

load_dotenv()

# Retrieval
TOP_K = 5
DOC_PATH = "data/unstructured/internal_docs.md"
DENSE_MODEL = "all-MiniLM-L6-v2"

# LLM Reasoning
CONFIDENCE_THRESHOLD = 0.5
MAX_TOKENS = 256

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# Monitoring
LATENCY_BASELINE_MS = 300
RECALL_BASELINE = 0.75
REFUSAL_BASELINE = 0.08

# App
APP_NAME = "SaaS-Product-Intelligence"
DEBUG = False
```

### Step 5: Update `app/llm/generator.py`

Replace the placeholder with OpenAI integration:

```python
"""LLM generator with OpenAI integration."""
import openai
from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from typing import Dict, List, Any

openai.api_key = OPENAI_API_KEY

def generate_answer(query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate answer using OpenAI API with context constraints.
    
    Args:
        query: User question
        contexts: List of retrieved documents
    
    Returns:
        {
            "answer": str,
            "citations": List[str],
            "confidence": float
        }
    """
    if not contexts:
        return {
            "answer": "No relevant context found.",
            "citations": [],
            "confidence": 0.0,
        }
    
    # Prepare context string
    context_text = "\n\n".join([
        f"Source {i+1}: {c['text'][:200]}" 
        for i, c in enumerate(contexts[:5])
    ])
    
    # System prompt enforces constraints
    system_prompt = """You are a product intelligence assistant. 
Your job is to answer questions about why metrics changed using ONLY the provided internal documentation.

CRITICAL RULES:
1. Answer ONLY using the provided context
2. Do NOT use external knowledge or make assumptions
3. Every factual claim must reference a source
4. If you're not sure, say so
5. Be concise (max 150 words)
6. Format citations as [Source N] at the end"""
    
    user_message = f"""Context from internal documentation:
{context_text}

Question: {query}

Answer using ONLY the provided context above. Include citations."""
    
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=256,
            timeout=10
        )
        
        answer_text = response.choices[0].message.content
        
        # Extract citations from answer
        citations = extract_citations(answer_text, contexts)
        
        # Compute confidence based on model response + context quality
        confidence = compute_confidence(contexts, answer_text)
        
        return {
            "answer": answer_text,
            "citations": citations,
            "confidence": confidence,
        }
    
    except openai.error.RateLimitError:
        return {
            "answer": "Rate limited. Please try again in a moment.",
            "citations": [],
            "confidence": 0.0,
        }
    except openai.error.AuthenticationError:
        return {
            "answer": "API key invalid. Check your OPENAI_API_KEY.",
            "citations": [],
            "confidence": 0.0,
        }
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "citations": [],
            "confidence": 0.0,
        }


def extract_citations(answer: str, contexts: List[Dict[str, Any]]) -> List[str]:
    """Extract citations from answer text."""
    citations = []
    for i, context in enumerate(contexts[:5]):
        source_text = context.get("text", "")[:100]
        if source_text.lower() in answer.lower() or f"[Source {i+1}]" in answer:
            citations.append(source_text)
    return citations[:3]  # Return top 3 citations


def compute_confidence(contexts: List[Dict[str, Any]], answer: str) -> float:
    """
    Compute confidence score.
    
    Factors:
    - Number of supporting documents
    - Document rank scores
    - Answer length (specificity)
    """
    n_docs = min(len(contexts), 3)
    doc_score = (n_docs / 3.0) * 0.4
    
    rank_score = (contexts[0].get("rank_score", 0.5) / 1.0) * 0.4
    
    answer_length_score = min(1.0, len(answer.split()) / 50.0) * 0.2
    
    return min(1.0, doc_score + rank_score + answer_length_score)
```

### Step 6: Test It

```bash
# Make sure .venv is activated
source .venv/bin/activate

# Start the server
python run.py
```

In another terminal:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Why did activation drop in March?"}'
```

You should now see **fluent, synthesized answers** instead of document extracts!

---

## Anthropic Integration

### Step 1: Get Your API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create account and navigate to **API Keys**
3. Create and copy your key

### Step 2: Install Dependencies

```bash
pip install anthropic python-dotenv
```

### Step 3: Create `.env` File

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229  # or claude-3-opus (more capable, slower)
ANTHROPIC_TEMPERATURE=0.3
```

### Step 4: Update `app/llm/generator.py`

```python
"""LLM generator with Anthropic integration."""
import anthropic
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_TEMPERATURE
from typing import Dict, List, Any

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_answer(query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate answer using Anthropic Claude API.
    
    Claude excels at following instructions and avoiding hallucination.
    """
    if not contexts:
        return {
            "answer": "No relevant context found.",
            "citations": [],
            "confidence": 0.0,
        }
    
    # Prepare context string
    context_text = "\n\n".join([
        f"Source {i+1}: {c['text'][:200]}" 
        for i, c in enumerate(contexts[:5])
    ])
    
    system_prompt = """You are a product intelligence assistant for a SaaS company.
Answer ONLY using the provided context. Do not use external knowledge.
Every answer must include [Source N] citations.
Be concise and specific."""
    
    user_message = f"""Context:
{context_text}

Question: {query}

Answer using the context above. Include citations."""
    
    try:
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=256,
            temperature=ANTHROPIC_TEMPERATURE,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        answer_text = message.content[0].text
        citations = extract_citations(answer_text, contexts)
        confidence = compute_confidence(contexts, answer_text)
        
        return {
            "answer": answer_text,
            "citations": citations,
            "confidence": confidence,
        }
    
    except anthropic.APIConnectionError as e:
        return {
            "answer": "Connection error. Check API key and internet.",
            "citations": [],
            "confidence": 0.0,
        }
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "citations": [],
            "confidence": 0.0,
        }


def extract_citations(answer: str, contexts: List[Dict[str, Any]]) -> List[str]:
    """Extract citations from answer text."""
    citations = []
    for i, context in enumerate(contexts[:5]):
        source_text = context.get("text", "")[:100]
        if source_text.lower() in answer.lower() or f"[Source {i+1}]" in answer:
            citations.append(source_text)
    return citations[:3]


def compute_confidence(contexts: List[Dict[str, Any]], answer: str) -> float:
    """Compute confidence score from context quality and answer specificity."""
    n_docs = min(len(contexts), 3)
    doc_score = (n_docs / 3.0) * 0.4
    
    rank_score = (contexts[0].get("rank_score", 0.5) / 1.0) * 0.4
    
    answer_length_score = min(1.0, len(answer.split()) / 50.0) * 0.2
    
    return min(1.0, doc_score + rank_score + answer_length_score)
```

---

## Other Providers

### Google Vertex AI

```python
from google.cloud import aiplatform
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/credentials.json'

def generate_answer(query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = aiplatform.gapic.PredictionServiceClient()
    # Implementation...
```

### Ollama (Local LLM)

```python
import requests

def generate_answer(query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama2", "prompt": prompt}
    )
    # Implementation...
```

---

## Testing Your Integration

### Unit Test

Create `tests/test_llm_integration.py`:

```python
import pytest
from app.llm.generator import generate_answer

def test_generate_answer_with_context():
    """Test answer generation with real context."""
    contexts = [
        {
            "text": "Release 2.3 caused a 20% activation drop due to UI changes.",
            "rank_score": 0.9
        },
        {
            "text": "The onboarding flow was redesigned in March.",
            "rank_score": 0.85
        }
    ]
    
    query = "Why did activation drop?"
    result = generate_answer(query, contexts)
    
    assert result["answer"] is not None
    assert len(result["answer"]) > 0
    assert result["confidence"] > 0.5
    assert len(result["citations"]) > 0


def test_generate_answer_empty_context():
    """Test graceful handling of empty context."""
    result = generate_answer("test query", [])
    
    assert result["answer"] is not None
    assert result["confidence"] == 0.0
    assert len(result["citations"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run it:

```bash
pytest tests/test_llm_integration.py -v
```

### Integration Test

```bash
# Start server
python run.py &

# Test with curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Why did activation drop in March?"}'

# Check response has answer + citations
```

### Cost Estimation

**OpenAI:**
- gpt-3.5-turbo: ~$0.0005 per query
- gpt-4: ~$0.003 per query

**Anthropic:**
- Claude 3 Sonnet: ~$0.003 per query
- Claude 3 Opus: ~$0.015 per query

For 1,000 queries/day with gpt-3.5-turbo: ~$150/month

---

## Troubleshooting

### "API key invalid"

```bash
# Check .env file exists
cat .env

# Verify key format (should start with sk-)
echo $OPENAI_API_KEY

# Check permissions
chmod 600 .env
```

### "Rate limited"

Add retry logic:

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def generate_answer_with_retry(query, contexts):
    return generate_answer(query, contexts)
```

### "Timeout"

Increase timeout in config:

```python
# app/config.py
REQUEST_TIMEOUT = 30  # seconds
```

Then use it:

```python
response = openai.ChatCompletion.create(
    ...,
    timeout=REQUEST_TIMEOUT
)
```

### "High latency"

- Use gpt-3.5-turbo instead of gpt-4
- Reduce context size (fewer documents)
- Enable caching with streaming

```python
# Streaming response for faster time-to-first-token
response = openai.ChatCompletion.create(
    ...,
    stream=True
)
for chunk in response:
    print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Production Checklist

- [ ] API key stored in `.env` (not in code)
- [ ] `.env` added to `.gitignore`
- [ ] Error handling for API failures
- [ ] Rate limiting configured
- [ ] Cost monitoring enabled
- [ ] System prompt enforces constraints
- [ ] Citations required in responses
- [ ] Confidence score computed
- [ ] Tests passing
- [ ] Latency under 2 seconds
- [ ] Graceful fallback if API down

---

## Next Steps

1. **Choose a provider** (OpenAI recommended for ease, Anthropic for safety)
2. **Follow steps 1-6** above for your chosen provider
3. **Run tests** to verify integration
4. **Monitor costs** using provider dashboard
5. **Iterate** on system prompt based on response quality

Questions? Check the [README.md](README.md) or [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md).
