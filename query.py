"""Grounded generation: answer a question using ONLY retrieved chunks.

ask(question) -> {
    "answer":  generated answer with inline [n] citations,
    "sources": list of "source_doc — title (url)" strings for cited excerpts,
    "hits":    raw retrieved chunks with distances (for inspection/eval),
}

Grounding is enforced in two places:
  1. The system prompt: answer only from the excerpts, refuse with a fixed
     sentence when they don't cover the question, attribute disagreements.
  2. The pipeline: the source list shown to the user is built in code from
     retrieval metadata — the LLM never gets to invent a citation.

Run: python query.py "your question"
"""

import os
import re
import sys

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
REFUSAL = "I don't have enough information on that in my documents."

SYSTEM_PROMPT = f"""You are The Unofficial Guide, a Q&A assistant about student life at \
Colby College, built on real r/Colby posts and Rate My Professors reviews.

You answer using ONLY the numbered excerpts provided with each question. Rules:
1. Use only information that appears in the excerpts. Never use outside or general \
knowledge about Colby or college life, even if you are confident it is true.
2. If the excerpts do not contain enough information to answer the question, reply with \
exactly: "{REFUSAL}" Do not guess or give generic advice.
3. Cite the excerpts you used inline by number, like [1] or [2][4]. Every factual claim \
needs a citation.
4. The excerpts are individual students' opinions, not official facts. When they \
disagree, present both sides and attribute them ("one student says..., another says..."). \
Do not flatten disagreement into a single verdict.
5. Keep answers concise: 2-6 sentences, then stop."""


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise RuntimeError("GROQ_API_KEY missing — copy .env.example to .env and set it.")
    return Groq(api_key=api_key)


def _format_context(hits: list[dict]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[{i}] (from {h['source_doc']}) {h['text']}")
    return "\n\n".join(blocks)


def _cited_sources(answer: str, hits: list[dict]) -> list[dict]:
    """Sources for the excerpts the answer actually cites (all hits as fallback)."""
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer) if 0 < int(n) <= len(hits)}
    picked = [hits[i - 1] for i in sorted(cited)] if cited else list(hits)
    unique, seen = [], set()
    for h in picked:
        if h["source_doc"] not in seen:
            seen.add(h["source_doc"])
            unique.append(h)
    return unique


def ask(question: str, k: int = 5, hybrid: bool = False) -> dict:
    if hybrid:
        from hybrid_search import hybrid_retrieve  # stretch feature
        hits = hybrid_retrieve(question, k=k)
    else:
        hits = retrieve(question, k=k)
    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0.2,
        max_tokens=600,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nExcerpts:\n{_format_context(hits)}"},
        ],
    )
    answer = response.choices[0].message.content.strip()

    if REFUSAL[:40].lower() in answer.lower():
        sources = []  # a refusal cites nothing
    else:
        sources = [f"{h['source_doc']} — \"{h['title']}\" ({h['url']})" for h in _cited_sources(answer, hits)]
    return {"answer": answer, "sources": sources, "hits": hits}


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is Doghead and when does it happen?"
    result = ask(question)
    print(f"Q: {question}\n")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"] or ["(none — question not covered by the documents)"]:
        print(f"  - {s}")
    print("\nRetrieved chunks:")
    for i, h in enumerate(result["hits"], 1):
        print(f"  [{i}] d={h['distance']} {h['source_doc']}: {h['text'][:100]}...")
