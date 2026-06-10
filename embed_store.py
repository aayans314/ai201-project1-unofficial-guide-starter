"""Embedding + vector store: embed chunks.json with all-MiniLM-L6-v2 and load
them into a persistent ChromaDB collection (cosine distance).

Run: python embed_store.py   (rebuilds the collection from scratch)
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("chunks.json")
DB_DIR = "chroma_db"
COLLECTION = "colby_guide"


def build():
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=DB_DIR)
    # Rebuild from scratch so re-running after a chunking change can't leave
    # stale chunks behind.
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks with all-MiniLM-L6-v2...")
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[
            {
                "source_doc": c["source_doc"],
                "source_type": c["source_type"],
                "title": c["title"],
                "url": c["url"],
                "date": c["date"],
                "position": c["position"],
            }
            for c in chunks
        ],
    )
    print(f"Stored {collection.count()} chunks in {DB_DIR}/ (collection '{COLLECTION}')")


if __name__ == "__main__":
    build()
