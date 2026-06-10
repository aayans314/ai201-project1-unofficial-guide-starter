"""One-off: find where specific answer chunks rank for the eval queries that
came back partially accurate (failure-case analysis for the README)."""

from retrieve import retrieve

CASES = [
    ("Can freshmen choose their dorm at Colby?", "sleep hours"),
    ("Can freshmen choose their dorm at Colby?", "freshman buildings"),
    ("Which dining halls do students recommend for lunch vs dinner?", "lunch at Foss"),
    ("Which dining halls do students recommend for lunch vs dinner?", "70%"),
]

for query, needle in CASES:
    hits = retrieve(query, k=40)
    rank = next((i for i, h in enumerate(hits, 1) if needle.lower() in h["text"].lower()), None)
    if rank:
        h = hits[rank - 1]
        print(f"query={query!r}\n  needle={needle!r} -> rank {rank}, d={h['distance']}, {h['source_doc']}")
        print(f"  text: {h['text'][:220]}")
    else:
        print(f"query={query!r}\n  needle={needle!r} -> NOT in top 40")
    print()
