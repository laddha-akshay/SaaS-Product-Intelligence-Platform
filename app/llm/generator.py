"""LLM generator placeholder."""


def generate_answer(query, contexts):
    txt = " ".join([c["text"] for c in contexts])
    return {
        "answer": txt[:300],
        "citations": [c["text"][:50] for c in contexts],
        "confidence": 0.75,
    }
