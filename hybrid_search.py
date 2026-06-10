"""Stretch feature: hybrid search — BM25 keyword scoring fused with semantic
search via Reciprocal Rank Fusion (RRF).

Why RRF instead of mixing raw scores: BM25 scores and cosine distances live
on completely different scales, so a weighted sum needs fragile tuning. RRF
only uses each method's RANKING: score(chunk) = sum over methods of
1 / (60 + rank). A chunk ranked well by both methods wins.

hybrid_retrieve(query, k=5) -> same shape as retrieve.retrieve(), with a
"found_by" field showing which method(s) ranked the chunk in their top-20.

Run: python hybrid_search.py   (writes stretch_hybrid_comparison.md)
"""

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from retrieve import retrieve

RRF_K = 60        # standard RRF constant
CANDIDATES = 20   # how deep each method's list goes before fusion

_chunks = None
_bm25 = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _load():
    global _chunks, _bm25
    if _chunks is None:
        _chunks = json.loads(Path("chunks.json").read_text(encoding="utf-8"))
        _bm25 = BM25Okapi([_tokenize(c["text"]) for c in _chunks])
    return _chunks, _bm25


def bm25_top(query: str, n: int = CANDIDATES) -> list[dict]:
    chunks, bm25 = _load()
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:n]
    return [
        {
            "text": chunks[i]["text"],
            "source_doc": chunks[i]["source_doc"],
            "title": chunks[i]["title"],
            "url": chunks[i]["url"],
            "date": chunks[i]["date"],
            "bm25_score": round(float(scores[i]), 2),
        }
        for i in ranked
    ]


def hybrid_retrieve(query: str, k: int = 5) -> list[dict]:
    semantic = retrieve(query, k=CANDIDATES)
    keyword = bm25_top(query, n=CANDIDATES)

    fused = {}
    for rank, hit in enumerate(semantic, 1):
        entry = fused.setdefault(hit["text"], {"hit": hit, "score": 0.0, "found_by": []})
        entry["score"] += 1.0 / (RRF_K + rank)
        entry["found_by"].append(f"semantic#{rank}")
    for rank, hit in enumerate(keyword, 1):
        entry = fused.setdefault(hit["text"], {"hit": hit, "score": 0.0, "found_by": []})
        entry["score"] += 1.0 / (RRF_K + rank)
        entry["found_by"].append(f"bm25#{rank}")

    best = sorted(fused.values(), key=lambda e: e["score"], reverse=True)[:k]
    out = []
    for e in best:
        hit = dict(e["hit"])
        hit["found_by"] = ", ".join(e["found_by"])
        hit.setdefault("distance", None)  # BM25-only hits have no cosine distance
        out.append(hit)
    return out


COMPARISON_QUERIES = [
    # exact-name queries where BM25 should help MiniLM out
    ("Which CS professor responds to emails quickly?", "responds email quicker"),
    ("Is Hillside a good place to live?", "Hillside"),
    ("What do students think of Professor Bender?", "Bender"),
    # the eval query where semantic-only struggled (answer at rank 3, d=0.537)
    ("Which dining halls do students recommend for lunch vs dinner?", "lunch at Foss"),
]


def needle_rank(hits, needle):
    for rank, h in enumerate(hits, 1):
        if needle.lower() in h["text"].lower():
            return rank
    return None


def main():
    lines = [
        "# Hybrid search (BM25 + semantic, RRF fusion) vs semantic-only",
        "",
        "Both methods produce a top-20 list; RRF fuses the two rankings",
        "(score = sum of 1/(60+rank)); top-5 of the fused list is returned.",
        "",
        "| Query | Needle | semantic-only | hybrid |",
        "|---|---|---|---|",
    ]
    for query, needle in COMPARISON_QUERIES:
        sem = needle_rank(retrieve(query, k=5), needle)
        hyb = needle_rank(hybrid_retrieve(query, k=5), needle)
        fmt = lambda r: f"hit @ rank {r}" if r else "MISS (not in top-5)"
        lines.append(f"| {query} | `{needle}` | {fmt(sem)} | {fmt(hyb)} |")
        print(lines[-1])

    lines += ["", "## Example: fused top-5 for an exact-name query", ""]
    for i, h in enumerate(hybrid_retrieve("Which CS professor responds to emails quickly?"), 1):
        lines.append(f"{i}. ({h['found_by']}) `{h['source_doc']}` — {h['text'][:140]}...")

    Path("stretch_hybrid_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nWrote stretch_hybrid_comparison.md")


if __name__ == "__main__":
    main()
