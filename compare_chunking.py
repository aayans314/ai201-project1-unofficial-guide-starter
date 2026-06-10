"""Stretch feature: chunking strategy comparison.

Compares three chunking strategies on the same documents and the same 5 eval
queries, holding everything else constant (same embedding model, same vector
store settings, no context prefixes for any strategy so the strategy itself
is the only variable):

  semantic  — my production strategy: comment/review hard boundaries +
              sentence-embedding topic-shift splits, 500 char cap, no overlap
  recursive — recursive character splitting over the whole document text
              (paragraph -> sentence -> word), 500 chars, 50 overlap
  fixed     — hard slice every 500 characters, no boundary awareness, no overlap

Metric: for each eval query, does the chunk containing the known answer text
(the "needle") appear in the top-5, at what rank, and at what distance.

Run: python compare_chunking.py   (writes stretch_chunking_comparison.md)
"""

import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunker import DOC_DIR, parse_document, semantic_split

MAX_CHARS = 500
OVERLAP = 50

QUERIES = [
    ("What is Doghead and when does it happen?", "library steps"),
    ("Can freshmen choose their dorm at Colby?", "chem-free dorm"),
    ("Do Colby dorms have air conditioning?", "pond houses"),
    ("Which dining halls do students recommend for lunch vs dinner?", "lunch at Foss"),
    ("How many on-campus Jan Plans are students expected to complete?", "3 on-campus JanPlans"),
]


def chunks_semantic(doc_text_units):
    """Production strategy minus the context prefix."""
    out = []
    for unit in doc_text_units:
        out.extend(semantic_split(unit))
    return out


def chunks_recursive(doc_text_units):
    """Recursive character splitting: try paragraphs, then sentences, then words."""
    text = "\n\n".join(doc_text_units)

    def split(piece, separators):
        if len(piece) <= MAX_CHARS:
            return [piece]
        if not separators:
            return [piece[i:i + MAX_CHARS] for i in range(0, len(piece), MAX_CHARS - OVERLAP)]
        sep, rest = separators[0], separators[1:]
        parts = [p for p in re.split(sep, piece) if p.strip()]
        if len(parts) == 1:
            return split(piece, rest)
        merged, current = [], ""
        for part in parts:
            candidate = f"{current} {part}".strip() if current else part
            if len(candidate) > MAX_CHARS and current:
                merged.append(current)
                current = f"{current[-OVERLAP:]} {part}".strip() if OVERLAP else part
            else:
                current = candidate
        if current:
            merged.append(current)
        return [s for m in merged for s in (split(m, rest) if len(m) > MAX_CHARS else [m])]

    return split(text, [r"\n\n", r"(?<=[.!?])\s+", r"\s+"])


def chunks_fixed(doc_text_units):
    """Naive fixed-length slicing across the whole document, no boundaries."""
    text = " ".join(doc_text_units)
    return [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]


def build_collection(client, name, strategy):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    ids, texts = [], []
    for path in sorted(DOC_DIR.glob("*.txt")):
        doc = parse_document(path)
        units = [text for _, text in doc["units"]]
        for i, chunk in enumerate(strategy(units)):
            if len(chunk.strip()) < 40:
                continue
            ids.append(f"{path.stem}_{i:03d}")
            texts.append(chunk.strip())
    col = client.create_collection(name, metadata={"hnsw:space": "cosine"})
    col.add(ids=ids, documents=texts,
            embeddings=model.encode(texts, normalize_embeddings=True).tolist())
    return col, len(texts)


def needle_rank(col, model, query, needle, k=5):
    res = col.query(query_embeddings=model.encode([query], normalize_embeddings=True).tolist(),
                    n_results=k)
    for rank, (doc, dist) in enumerate(zip(res["documents"][0], res["distances"][0]), 1):
        if needle.lower() in doc.lower():
            return rank, round(dist, 3), round(res["distances"][0][0], 3)
    return None, None, round(res["distances"][0][0], 3)


def build_production_collection(client):
    """Fourth variant: the actual production chunks (semantic + context prefix),
    straight from chunks.json — shows what the prefix adds on top of the split."""
    import json

    chunks = json.loads(Path("chunks.json").read_text(encoding="utf-8"))
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    col = client.create_collection("production", metadata={"hnsw:space": "cosine"})
    col.add(ids=[c["id"] for c in chunks], documents=texts,
            embeddings=model.encode(texts, normalize_embeddings=True).tolist())
    return col, len(texts)


def main():
    client = chromadb.EphemeralClient()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    strategies = {
        "semantic": chunks_semantic,
        "recursive": chunks_recursive,
        "fixed": chunks_fixed,
    }

    cols, counts = {}, {}
    for name, fn in strategies.items():
        print(f"Building '{name}' collection...")
        cols[name], counts[name] = build_collection(client, name, fn)
        print(f"  {counts[name]} chunks")
    print("Building 'semantic+prefix (production)' collection...")
    cols["semantic+prefix"], counts["semantic+prefix"] = build_production_collection(client)
    strategies["semantic+prefix"] = None

    lines = [
        "# Chunking strategy comparison",
        "",
        "Same documents, same embedding model (all-MiniLM-L6-v2), same eval queries.",
        "No context prefixes for any strategy, so the split logic is the only variable.",
        "Hit = the chunk containing the known answer text appears in the top-5.",
        "",
        "Chunk counts: " + ", ".join(f"{n}={c}" for n, c in counts.items()),
        "",
        "| Query | Needle | " + " | ".join(strategies) + " |",
        "|---|---|" + "---|" * len(strategies),
    ]

    score = {name: 0 for name in strategies}
    for query, needle in QUERIES:
        row = [query, f"`{needle}`"]
        for name in strategies:
            rank, dist, top1 = needle_rank(cols[name], model, query, needle)
            if rank:
                score[name] += 1
                row.append(f"hit @ rank {rank} (d={dist})")
            else:
                row.append(f"MISS (top-1 d={top1})")
        lines.append("| " + " | ".join(row) + " |")

    lines += ["", "Hits out of 5: " + ", ".join(f"{n}={s}" for n, s in score.items())]
    Path("stretch_chunking_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
