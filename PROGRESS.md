# Project Progress Tracker

Working checklist for Project 1 (The Unofficial Guide). Checking things off as they get done so nothing from the rubric slips through.

**Domain:** Student life + academics at Colby College
**Sources:** r/Colby subreddit threads + Rate My Professors reviews

---

## Milestones

- [x] M1: Choose domain + collect 10+ documents (19 docs: 13 r/Colby threads via PullPush + 6 RMP professor review sets via GraphQL, raw JSON in `data_raw/`)
- [x] M2: planning.md complete (all sections, before pipeline code)
- [ ] M3: Ingestion + cleaning + chunking pipeline, chunks inspected
- [ ] M4: Embedding + ChromaDB + retrieval tested on 3+ eval queries
- [ ] M5: Grounded generation + source attribution + Gradio interface
- [ ] M6: Evaluation report, README, failure analysis
- [ ] Demo video (recorded by me — script/queries prepared)

## Rubric — Required (25 pts)

### Document Pipeline (3)
- [ ] README names domain + 10 documents w/ specific sources
- [ ] Chunking strategy explained: size, overlap, why it fits these docs
- [ ] 5+ labeled sample chunks w/ source document names in README

### Retrieval (4)
- [ ] 3+ retrieval test examples in README (query + top chunks)
- [ ] Written relevance explanation for at least 2 of them
- [ ] Embedding model named
- [ ] Production tradeoff reflection (cost, context length, multilingual, local vs API)

### Grounded Generation (3)
- [ ] 2+ example responses with visible source attribution
- [ ] 1 out-of-scope query with refusal response shown
- [ ] Grounding enforcement explained (prompt + pipeline structure)

### Evaluation Report (4)
- [ ] All 5 questions: question, expected answer, actual response
- [ ] Accuracy judgment for each (accurate / partial / inaccurate)
- [ ] 1+ failure case with specific cause tied to a pipeline stage

### Query Interface (2)
- [ ] Input/output fields described in README
- [ ] Sample interaction transcript (complete query + response)

### planning.md (4)
- [x] Domain: named + why hard to find officially
- [x] Documents (10+ specific) / Chunking (size, overlap, fit) / Retrieval (model, top-k, tradeoffs)
- [x] Evaluation plan: 5 specific verifiable Q&A pairs
- [x] 2+ anticipated challenges / AI tool plan naming components
- [x] Stretch features planned in planning.md before implementation

### README Completeness (3)
- [ ] Domain, sources, chunking, embedding, grounding all covered
- [ ] Full eval report
- [ ] Failure case + spec reflection (1 way it helped, 1 divergence + why)

### AI Usage (2)
- [ ] 2+ specific instances: what was directed, what was produced
- [ ] What was reviewed/revised/overridden in each

## Rubric — Stretch (+5 bonus)

- [ ] Chunking comparison (+1): 2+ strategies on same query set, which won + why
- [ ] Hybrid search (+2): BM25 + semantic combination, comparison on 3+ queries
- [ ] Metadata filtering (+1): filter by source/date/rating with visible effect
- [ ] Conversational memory (+1): multi-turn query referencing earlier context
- [ ] planning.md updated BEFORE starting each stretch feature

## Reminders

- [ ] Commit at every milestone (at least one per milestone)
- [ ] Never commit .env
- [ ] Test retrieval before generation
- [ ] Distance scores on top results should be < 0.5
- [ ] Eval must surface at least one real failure
- [ ] Video: 3+ cited queries, 1 good case, 1 failure case, eval walkthrough
