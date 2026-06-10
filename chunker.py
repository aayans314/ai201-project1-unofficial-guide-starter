"""Chunking: split cleaned documents (documents/*.txt) into retrieval chunks.

Strategy (see planning.md "Chunking Strategy"):
  - A comment / review / post is a HARD boundary: a chunk never mixes two
    people's writing.
  - Units under MAX_CHARS become a single chunk.
  - Longer units are split semantically: sentences are embedded with
    all-MiniLM-L6-v2 and the unit is broken where similarity between adjacent
    sentences drops (a topic shift), or where the MAX_CHARS cap forces it.
  - No overlap.
  - Every chunk is prefixed with a short context tag (thread title or
    professor name) so it stands alone when retrieved.

Output: chunks.json — list of {id, text, source_doc, source_type, title, url,
date, position}.

Run: python chunker.py   (prints stats + 5 random chunks for inspection)
"""

import json
import random
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DOC_DIR = Path("documents")
OUT_FILE = Path("chunks.json")

MAX_CHARS = 500   # cap per chunk body
MIN_CHARS = 150   # don't split for a topic shift before a chunk has this much
MIN_KEEP = 40     # merge/drop fragments smaller than this

UNIT_RE = re.compile(r"^(POST|COMMENT|SUMMARY|REVIEW(?: \([^)]*\))?):\s*(.+)$")

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def hard_wrap(text: str, limit: int) -> list[str]:
    """Fallback for a single run-on sentence longer than the cap."""
    words, pieces, current = text.split(), [], ""
    for w in words:
        if current and len(current) + 1 + len(w) > limit:
            pieces.append(current)
            current = w
        else:
            current = f"{current} {w}".strip()
    if current:
        pieces.append(current)
    return pieces


def semantic_split(text: str) -> list[str]:
    """Split one unit's text into <=MAX_CHARS pieces at topic-shift boundaries."""
    if len(text) <= MAX_CHARS:
        return [text]

    sentences = split_sentences(text)
    sentences = [p for s in sentences for p in (hard_wrap(s, MAX_CHARS) if len(s) > MAX_CHARS else [s])]
    if len(sentences) == 1:
        return sentences

    embeddings = get_model().encode(sentences, normalize_embeddings=True)
    sims = np.array([float(embeddings[i] @ embeddings[i + 1]) for i in range(len(sentences) - 1)])
    # "Topic shift" = adjacent similarity unusually low for this unit.
    threshold = sims.mean() - sims.std()

    pieces, current = [], sentences[0]
    for i in range(1, len(sentences)):
        sent = sentences[i]
        would_exceed = len(current) + 1 + len(sent) > MAX_CHARS
        topic_shift = sims[i - 1] < threshold and len(current) >= MIN_CHARS
        if would_exceed or topic_shift:
            pieces.append(current)
            current = sent
        else:
            current = f"{current} {sent}"
    pieces.append(current)

    # A tiny trailing fragment is not retrievable on its own — glue it back
    # only if that doesn't blow the cap, otherwise keep it (rare).
    merged = []
    for p in pieces:
        if merged and len(p) < MIN_KEEP and len(merged[-1]) + 1 + len(p) <= MAX_CHARS:
            merged[-1] = f"{merged[-1]} {p}"
        else:
            merged.append(p)
    return merged


def parse_document(path: Path) -> dict:
    meta, units = {}, []
    for para in path.read_text(encoding="utf-8").split("\n"):
        line = para.strip()
        if not line:
            continue
        for key in ("TITLE", "SOURCE", "TYPE", "DATE"):
            if line.startswith(f"{key}: "):
                meta[key.lower()] = line[len(key) + 2:]
                break
        else:
            m = UNIT_RE.match(line)
            if m:
                units.append((m.group(1), m.group(2)))
    meta["units"] = units
    return meta


def context_prefix(doc: dict, unit_kind: str) -> str:
    if doc["type"] == "reddit_thread":
        return f'[r/Colby thread "{doc["title"]}", {doc["date"]}]'
    # RMP: "Rate My Professors reviews of NAME (DEPT, Colby College)"
    name = re.sub(r"^Rate My Professors reviews of ", "", doc["title"])
    name = re.sub(r" \(.*\)$", "", name)
    if unit_kind.startswith("REVIEW"):
        detail = unit_kind[len("REVIEW "):].strip("()")  # "CS231, 2019-11"
        return f"[RMP review of {name} ({detail})]"
    return f"[RMP profile of {name}]"


def chunk_documents() -> list[dict]:
    chunks = []
    for path in sorted(DOC_DIR.glob("*.txt")):
        doc = parse_document(path)
        position = 0
        for kind, text in doc["units"]:
            for piece in semantic_split(text):
                if len(piece) < MIN_KEEP:
                    continue
                chunks.append({
                    "id": f"{path.stem}_{position:03d}",
                    "text": f"{context_prefix(doc, kind)} {piece}",
                    "source_doc": path.name,
                    "source_type": doc["type"],
                    "title": doc["title"],
                    "url": doc["source"],
                    "date": doc["date"],
                    "position": position,
                })
                position += 1
    return chunks


def main():
    chunks = chunk_documents()
    OUT_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    lengths = [len(c["text"]) for c in chunks]
    by_doc = {}
    for c in chunks:
        by_doc[c["source_doc"]] = by_doc.get(c["source_doc"], 0) + 1

    print(f"Total chunks: {len(chunks)}")
    print(f"Length (chars): min={min(lengths)} median={int(np.median(lengths))} max={max(lengths)}")
    print("\nChunks per document:")
    for doc, n in sorted(by_doc.items()):
        print(f"  {doc}: {n}")

    print("\n--- 5 random chunks for inspection ---")
    random.seed(7)
    for c in random.sample(chunks, 5):
        print(f"\n[{c['id']}] ({len(c['text'])} chars)\n{c['text']}")


if __name__ == "__main__":
    main()
