# Chunking strategy comparison

Same documents, same embedding model (all-MiniLM-L6-v2), same eval queries.
No context prefixes for any strategy, so the split logic is the only variable.
Hit = the chunk containing the known answer text appears in the top-5.

Chunk counts: semantic=257, recursive=222, fixed=147, semantic+prefix=257

| Query | Needle | semantic | recursive | fixed | semantic+prefix |
|---|---|---|---|---|---|
| What is Doghead and when does it happen? | `library steps` | hit @ rank 1 (d=0.488) | hit @ rank 1 (d=0.556) | MISS (top-1 d=0.6) | hit @ rank 1 (d=0.475) |
| Can freshmen choose their dorm at Colby? | `chem-free dorm` | MISS (top-1 d=0.306) | MISS (top-1 d=0.306) | hit @ rank 2 (d=0.356) | hit @ rank 5 (d=0.356) |
| Do Colby dorms have air conditioning? | `pond houses` | MISS (top-1 d=0.17) | hit @ rank 1 (d=0.425) | hit @ rank 1 (d=0.25) | hit @ rank 3 (d=0.369) |
| Which dining halls do students recommend for lunch vs dinner? | `lunch at Foss` | hit @ rank 3 (d=0.368) | MISS (top-1 d=0.321) | MISS (top-1 d=0.309) | hit @ rank 3 (d=0.537) |
| How many on-campus Jan Plans are students expected to complete? | `3 on-campus JanPlans` | hit @ rank 1 (d=0.283) | hit @ rank 1 (d=0.337) | hit @ rank 1 (d=0.365) | hit @ rank 1 (d=0.289) |

Hits out of 5: semantic=3, recursive=3, fixed=3, semantic+prefix=5