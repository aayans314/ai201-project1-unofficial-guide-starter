"""Retrieval: semantic search over the ChromaDB collection.

retrieve(query, k=5) -> list of {text, source_doc, title, url, date, distance}

Run: python retrieve.py "your question here"   (prints chunks + distances)
"""

import sys

import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION = "colby_guide"
TOP_K = 5

_model = None
_collection = None


def _load():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _collection = chromadb.PersistentClient(path=DB_DIR).get_collection(COLLECTION)
    return _model, _collection


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    model, collection = _load()
    embedding = model.encode([query], normalize_embeddings=True)
    result = collection.query(query_embeddings=embedding.tolist(), n_results=k)
    return [
        {
            "text": doc,
            "source_doc": meta["source_doc"],
            "title": meta["title"],
            "url": meta["url"],
            "date": meta["date"],
            "distance": round(dist, 3),
        }
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is Doghead and when does it happen?"
    print(f"QUERY: {question}\n")
    for i, hit in enumerate(retrieve(question), 1):
        print(f"--- #{i} (distance {hit['distance']}) from {hit['source_doc']}")
        print(hit["text"])
        print()
