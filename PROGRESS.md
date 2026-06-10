# Project Progress Tracker

Working checklist for Project 1 (The Unofficial Guide). Checking things off as they get done so nothing from the rubric slips through.

**Domain:** Student life + academics at Colby College
**Sources:** r/Colby subreddit threads + Rate My Professors reviews

---

## Milestones

- [x] M1: Choose domain + collect 10+ documents (19 docs: 13 r/Colby threads via PullPush + 6 RMP professor review sets via GraphQL, raw JSON in `data_raw/`)
- [x] M2: planning.md complete (all sections, before pipeline code)
- [x] M3: Ingestion + cleaning + chunking pipeline, chunks inspected (257 chunks, median 321 chars)
- [x] M4: Embedding + ChromaDB + retrieval tested on all 5 eval queries (4/5 top hits < 0.5 distance; dining query weakest at 0.537 rank 3 — noted for failure analysis)
- [x] M5: Grounded generation + source attribution + Gradio interface (refusal tested on 2 out-of-scope queries; UI verified end-to-end on port 7860)
- [x] M6: Evaluation report, README, failure analysis (3 accurate, 2 partial, refusal verified; failure traced to reply-chunk losing parent context)
- [ ] Demo video (recorded by me — script/queries prepared)

## Rubric — Required (25 pts)

### Document Pipeline (3)
- [x] README names domain + 10 documents w/ specific sources
- [x] Chunking strategy explained: size, overlap, why it fits these docs
- [x] 5+ labeled sample chunks w/ source document names in README

### Retrieval (4)
- [x] 3+ retrieval test examples in README (query + top chunks)
- [x] Written relevance explanation for at least 2 of them
- [x] Embedding model named
- [x] Production tradeoff reflection (cost, context length, multilingual, local vs API)

### Grounded Generation (3)
- [x] 2+ example responses with visible source attribution
- [x] 1 out-of-scope query with refusal response shown
- [x] Grounding enforcement explained (prompt + pipeline structure)

### Evaluation Report (4)
- [x] All 5 questions: question, expected answer, actual response
- [x] Accuracy judgment for each (accurate / partial / inaccurate)
- [x] 1+ failure case with specific cause tied to a pipeline stage

### Query Interface (2)
- [x] Input/output fields described in README
- [x] Sample interaction transcript (complete query + response)

### planning.md (4)
- [x] Domain: named + why hard to find officially
- [x] Documents (10+ specific) / Chunking (size, overlap, fit) / Retrieval (model, top-k, tradeoffs)
- [x] Evaluation plan: 5 specific verifiable Q&A pairs
- [x] 2+ anticipated challenges / AI tool plan naming components
- [x] Stretch features planned in planning.md before implementation

### README Completeness (3)
- [x] Domain, sources, chunking, embedding, grounding all covered
- [x] Full eval report
- [x] Failure case + spec reflection (1 way it helped, 1 divergence + why)

### AI Usage (2)
- [x] 2+ specific instances: what was directed, what was produced
- [x] What was reviewed/revised/overridden in each

## Rubric — Stretch (+5 bonus)

- [x] Chunking comparison (+1): 2+ strategies on same query set, which won + why
- [x] Hybrid search (+2): BM25 + semantic combination, comparison on 3+ queries
- [ ] Metadata filtering (+1): filter by source/date/rating with visible effect
- [ ] Conversational memory (+1): multi-turn query referencing earlier context
- [x] planning.md updated BEFORE starting each stretch feature

## Reminders

- [x] Commit at every milestone (at least one per milestone)
- [x] Never commit .env
- [x] Test retrieval before generation
- [x] Distance scores on top results should be < 0.5
- [x] Eval must surface at least one real failure
- [ ] Video: 3+ cited queries, 1 good case, 1 failure case, eval walkthrough
