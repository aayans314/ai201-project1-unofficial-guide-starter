"""Quick retrieval smoke test: run eval-plan queries and print top chunks."""

from retrieve import retrieve

QUERIES = [
    "Can freshmen choose their dorm at Colby?",
    "Do Colby dorms have air conditioning?",
    "Which dining halls do students recommend for lunch vs dinner?",
    "How many on-campus Jan Plans are students expected to complete?",
]

for q in QUERIES:
    print("=" * 25, q)
    for i, h in enumerate(retrieve(q), 1):
        print(f"  #{i} d={h['distance']} [{h['source_doc']}] {h['text'][:160]}")
    print()
