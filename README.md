# The Unofficial Guide — Project 1

A RAG system that answers plain-language questions about student life at Colby College, grounded in real r/Colby threads and Rate My Professors reviews, with sources cited on every answer.

**Quick start:**

```
pip install -r requirements.txt
# copy .env.example to .env and add your Groq key, then:
python ingest.py        # raw JSON -> cleaned documents/
python chunker.py       # documents/ -> chunks.json (semantic chunking)
python embed_store.py   # chunks.json -> chroma_db/
python app.py           # Gradio UI at http://localhost:7860
```

---

## Domain

Student life and academics at Colby College. I'm a Colby student, and the most useful knowledge about this school — that freshmen get almost no say in housing, that only the Johnson Pond houses have AC, what Doghead actually is, which CS professors are worth taking — never appears on the official site. It lives in scattered r/Colby threads and Rate My Professors reviews going back years. This system makes that knowledge searchable: you ask a question, it retrieves what students actually wrote, and answers only from that, with the sources attached.

---

## Document Sources

19 documents: 13 r/Colby threads (a thread plus all its comments = one document) and 6 RMP review pages for Colby CS professors.

Collection note: Reddit returns 403 to scripted requests from my machine on every host I tried (www, old, api), so threads were pulled through the PullPush archive API (api.pullpush.io), which mirrors Reddit. RMP reviews came from RMP's public GraphQL endpoint (the same data the professor pages render). All raw JSON is committed under `data_raw/` so the pipeline is reproducible.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | "I got into Colby a few days ago, and I wanted to ask some questions :)" (21 comments, 2022) | r/Colby thread | reddit.com/r/Colby/comments/tkrwaw/ |
| 2 | "Questions for Colby students / alumni :))" (19 comments, 2022) | r/Colby thread | reddit.com/r/Colby/comments/txeni4/ |
| 3 | "Q&A for Prospective students:" (18 comments, 2022) | r/Colby thread | reddit.com/r/Colby/comments/tq60un/ |
| 4 | "Choosing courses for freshman year" (18 comments, 2021) | r/Colby thread | reddit.com/r/Colby/comments/n4v3ml/ |
| 5 | "Can i get some advice?" (17 comments, 2024) | r/Colby thread | reddit.com/r/Colby/comments/1es4ej8/ |
| 6 | "Banned Items at Colby Dorms?" (14 comments, 2022) | r/Colby thread | reddit.com/r/Colby/comments/znvc3i/ |
| 7 | "Best language?" (10 comments, 2023) | r/Colby thread | reddit.com/r/Colby/comments/14rqze0/ |
| 8 | "Is the social life here bad?" (7 comments, 2023) | r/Colby thread | reddit.com/r/Colby/comments/1363wjz/ |
| 9 | "Is the food actually that bad?" (6 comments, 2021) | r/Colby thread | reddit.com/r/Colby/comments/md5xv5/ |
| 10 | "housing for freshman" (6 comments, 2022) | r/Colby thread | reddit.com/r/Colby/comments/v1vydc/ |
| 11 | "So freshmen have no say on their housing?" (5 comments, 2023) | r/Colby thread | reddit.com/r/Colby/comments/18pfyod/ |
| 12 | "AS231 (Introduction to Astrophysics) Review and Advice" (4 comments, 2024) | r/Colby thread | reddit.com/r/Colby/comments/1dx0v18/ |
| 13 | "Winter coat and boots recommendations?" (3 comments, 2024) | r/Colby thread | reddit.com/r/Colby/comments/1cp7ve6/ |
| 14 | Dale Skrien, CS — 16 reviews (he's no longer at Colby, but the reviews are useful history) | RMP | ratemyprofessors.com/professor/364345 |
| 15 | Oliver Layton, CS — 12 reviews | RMP | ratemyprofessors.com/professor/2442672 |
| 16 | Stephanie R. Taylor, CS — 11 reviews | RMP | ratemyprofessors.com/professor/1327389 |
| 17 | Bilal Ahmad, CS — 11 reviews | RMP | ratemyprofessors.com/professor/1841040 |
| 18 | Maximillian Bender, CS — 8 reviews | RMP | ratemyprofessors.com/professor/2899686 |
| 19 | Allen Harper, CS — 6 reviews | RMP | ratemyprofessors.com/professor/2867220 |

I collected one more thread ("The Waterville Secret that Everyone Knows", 21 comments) and cut it after actually reading it — it's true-crime gossip about a named local person, not student-life knowledge, and I didn't want my system citing it.

---

## Chunking Strategy

**Chunk size:** semantic, capped at ~500 characters (~100–125 tokens). A chunk ends where the topic shifts or where the natural unit ends, whichever comes first.

**Overlap:** none.

**Preprocessing before chunking** (`ingest.py`): parse the raw PullPush/RMP JSON; drop `[deleted]`/`[removed]` comments; drop bot comments (the corpus had a book bot, a grammar bot, and "bad bot" replies — filtered by author name and body signatures like "I'm a bot" / "beep boop"); drop comments under 40 characters ("Same!", "thank you" add nothing retrievable); unescape HTML entities (`&amp;`, `&gt;` — PullPush double-escapes some); strip markdown links, emphasis markers, quoted parent text, and invisible unicode junk. Output is one clean text file per document with one unit (post / comment / review) per paragraph.

**Why these choices fit my documents:** the corpus is almost entirely short self-contained units — Reddit comments and RMP reviews. So the chunker (`chunker.py`) works like this:

1. A comment/review is a **hard boundary**: a chunk never mixes two people's writing, because gluing two opinions together breaks both meaning and attribution.
2. Most units are under 500 chars and become exactly one chunk.
3. Long units (some comments run 800–1500 chars across multiple topics) get split *semantically*: each sentence is embedded with MiniLM, and the unit is split where similarity between adjacent sentences drops below that unit's mean minus one standard deviation (a topic shift), or where the 500-char cap forces it.
4. No overlap, because the natural units are self-contained; overlap would mostly duplicate short comments. The accepted risk (it shows up in my failure case below) is that a fact spanning a split point can become unretrievable.
5. Every chunk gets a short bracketed context prefix — the thread title or professor/course — so a chunk like "It might trip your fuse..." still makes sense alone. The prefix turned out to matter a lot (see the chunking comparison stretch results).

**Final chunk count:** 257 chunks across 19 documents (min 93 chars, median 321, max 590 — the max exceeds 500 because the cap applies to the body and the context prefix is added after).

### Sample chunks

1. From `reddit_znvc3i.txt`:
   > [r/Colby thread "Banned Items at Colby Dorms?", 2022-12] Heaters, yes. Air conditioners are in the Jonson pond houses only. That being said, you'll want an air conditioner for about two weeks total. Just make sure to bring a fan!

2. From `rmp_oliver_layton_2442672.txt`:
   > [RMP review of Oliver Layton (CS231, 2019-11)] Oliver is amazing! His lectures are VERY well-organized. Plus, I've never seen any professor who responds email quicker than he does. I took my first CS course at Colby with him and truly ENJOYED everything! He's being super supportive and is always willing to help you outside class. He's also a very nice guy to talk to. [Quality: 5/5, Difficulty: 3/5] [Tags: Accessible outside class, Amazing lectures, Caring]

3. From `reddit_tq60un.txt`:
   > [r/Colby thread "Q&A for Prospective students:", 2022-03] For JanPlan: I think the rules still in place are that every student is expected to complete 3 on-campus JanPlans during their time at Colby, with Freshman year being one of them. People have been able to propose personal alternatives to these, but it does take some effort and the school can say no. Of the "on-campus" courses though, some involve travel. One for example spends two weeks on campus studying geology then goes to Bermuda for the second half of Jan Plan.

4. From `reddit_18pfyod.txt`:
   > [r/Colby thread "So freshmen have no say on their housing?", 2023-12] Colby won't always accommodate them, from experience. Maybe if you have one or two minor needs that need meeting. Otherwise, it takes a lot of talking to accommodations and then housing to make sure that your needs are met

5. From `reddit_n4v3ml.txt` (an honest example of the no-overlap tradeoff — this is the second half of a long comment recommending MA161, and the course name lives in the *previous* chunk):
   > [r/Colby thread "Choosing courses for freshman year", 2021-05] There's many reason for this: 1. It's a tremendously fun class 2. It is proof-based, and as such the only real math class you can really take now. This adds to the fun: it's based on Spivak's calculus, which is sort of the bible of undergrad calculus built from the ground up... and I mean from the ground up! You'll learn the basic building blocks of math. 3. It's hard. This is a good thing: it's a little less hard than other math classes, but it will give you a good idea of what you're in for.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers (384-dim, 256-token window), running locally; stored in ChromaDB with cosine distance. My chunks max out around 125 tokens, so they fit the window comfortably.

**Production tradeoff reflection:** for a real deployment I'd weigh: (1) **cost and privacy** — MiniLM is free and queries never leave the machine; an API model (OpenAI text-embedding-3, Cohere) bills per token and ships student queries to a third party; (2) **domain vocabulary** — "JanPlan," "Doghead," "Foss," "MA161" are exactly where a small general model is weakest, and my hybrid-search results confirm exact-name queries are the soft spot; a larger model would likely close some of that gap; (3) **context length** — 256 tokens is fine for comment-sized chunks but would force awkward chunking for long handbooks; (4) **multilingual support** — irrelevant for r/Colby, but a tool aimed at international applicants would need it and MiniLM is weak there; (5) **latency/scale** — local CPU inference beats an API round-trip at my size, but serving thousands of concurrent users would need GPU serving or an API anyway.

---

## Grounded Generation

**System prompt grounding instruction** (the actual prompt from `query.py`):

> You answer using ONLY the numbered excerpts provided with each question. Rules:
> 1. Use only information that appears in the excerpts. Never use outside or general knowledge about Colby or college life, even if you are confident it is true.
> 2. If the excerpts do not contain enough information to answer the question, reply with exactly: "I don't have enough information on that in my documents." Do not guess or give generic advice.
> 3. Cite the excerpts you used inline by number, like [1] or [2][4]. Every factual claim needs a citation.
> 4. The excerpts are individual students' opinions, not official facts. When they disagree, present both sides and attribute them ("one student says..., another says..."). Do not flatten disagreement into a single verdict.
> 5. Keep answers concise: 2-6 sentences, then stop.

Rule 4 exists because my corpus genuinely disagrees with itself (the food debate spans "pretty good" to "food quality is ass" across threads), and I didn't want the model laundering a contested opinion into a fact.

**How source attribution is surfaced:** two layers. The model cites excerpt numbers inline ([1], [2]) — but the source list shown under every answer is built **in code** from retrieval metadata (`_cited_sources()` in `query.py` maps the cited numbers back to document names and URLs). The LLM never gets the chance to invent a citation. If the model refuses, the source list is empty on purpose — a refusal cites nothing. Generation is Groq `llama-3.3-70b-versatile` at temperature 0.2.

---

## Retrieval Tests

Three of my eval queries, with the top retrieved chunks and distances (full top-5 for all queries is in `eval_results.md`):

**Query 1: "What is Doghead and when does it happen?"**

| rank | distance | source | chunk (truncated) |
|---|---|---|---|
| 1 | 0.475 | reddit_tkrwaw.txt | "...Doghead is definitely the biggest tradition on campus. It's sort of a st Patrick's day celebration that happens on the weekend before Spring break. Basically people stay up celebrating all night and anyone who manages to stay up goes to watch the sunrise from the library steps..." |
| 2 | 0.655 | reddit_txeni4.txt | "...The biggest day of the year, Doghead, is dedicated to getting plastered for 24 hours." |
| 3 | 0.769 | reddit_tkrwaw.txt | (New England weather variability) |

*Why these are relevant:* the rank-1 chunk is the single best answer in the entire corpus — it defines Doghead, gives its timing, and describes the all-nighter and sunrise. Rank 2 is the other thread's (blunter) description of the same event, which gives the answer a second perspective to attribute. Rank 3 is where relevance falls off — it matched on campus-life vocabulary, not on Doghead — which is visible in the distance jump from 0.655 to 0.769.

**Query 2: "Can freshmen choose their dorm at Colby?"**

| rank | distance | source | chunk (truncated) |
|---|---|---|---|
| 1 | 0.280 | reddit_18pfyod.txt | "they're very limited, but any person who wants to move can apply to be settled in those free spots... if you have any physical and/or mental conditions... you might even get higher priority than seniors..." |
| 2 | 0.290 | reddit_18pfyod.txt | "Colby won't always accommodate them, from experience..." |
| 5 | 0.356 | reddit_18pfyod.txt | "...the only thing you can request is a chem-free dorm. Everything else is just random and other preferences aren't considered at all?" |

*Why these are relevant:* all three come from the one thread that's literally titled "So freshmen have no say on their housing?", and together they cover the answer: choice is minimal (rank 5: chem-free is the only request), with a real accommodations process as the exception (ranks 1–2, which also disagree with each other about how well it works — the generated answer attributes both).

**Query 3: "How many on-campus Jan Plans are students expected to complete?"**

| rank | distance | source | chunk (truncated) |
|---|---|---|---|
| 1 | 0.289 | reddit_tq60un.txt | "For JanPlan: I think the rules still in place are that every student is expected to complete 3 on-campus JanPlans... with Freshman year being one of them..." |
| 2 | 0.321 | reddit_tq60un.txt | "Typically, most students take the school's Jan Plan courses. These are more intensive than a normal course..." |
| 5 | 0.493 | reddit_tq60un.txt | "So internships aren't considered an on-campus Jan Plan so it's not common for first years..." |

The exact answer is rank 1 at d=0.289, with supporting context behind it.

---

## Example Responses

**Example 1** (source attribution visible in output):

> **Q: What is Doghead and when does it happen?**
>
> Doghead is a tradition on campus that is sort of a St. Patrick's Day celebration [1]. It happens on the weekend before Spring break [1]. One student describes it as a 24-hour event where people get "plastered" [2], while another student notes that it's a fun and lively event where people try to stay up all night and watch the sunrise from the library steps [1][4].
>
> Sources:
> • reddit_tkrwaw.txt — "I got into Colby a few days ago, and I wanted to ask some questions :)" (https://www.reddit.com/r/Colby/comments/tkrwaw/)
> • reddit_txeni4.txt — "Questions for Colby students / alumni :))" (https://www.reddit.com/r/Colby/comments/txeni4/)

**Example 2** (disagreement attributed, not flattened):

> **Q: Can freshmen choose their dorm at Colby?**
>
> One student says that freshmen have very limited choice in their housing, but can apply to fill free spots [1]. However, another student notes that Colby won't always accommodate individual needs, unless they are minor [2]. According to a post, the only thing freshmen can request is a chem-free dorm, and other preferences are not considered [5]. It appears that freshmen do not have much control over their dorm choice, except for possibly requesting a substance-free dorm [5].
>
> Sources:
> • reddit_18pfyod.txt — "So freshmen have no say on their housing?" (https://www.reddit.com/r/Colby/comments/18pfyod/)

**Out-of-scope query** (refusal):

> **Q: How much does tuition cost at Colby?**
>
> I don't have enough information on that in my documents.
>
> Sources: (none — question not covered by the documents)

Retrieval did return loosely related chunks for this one (a comment about using the net price calculator, d=0.438), but the model correctly recognized none of them contain a tuition figure and refused instead of improvising. Same behavior on a fully off-topic probe ("best restaurant in Portland, Maine").

---

## Query Interface

Gradio web UI (`python app.py`, then http://localhost:7860).

**Inputs:** a free-text question box, and a checkbox to switch retrieval from semantic-only to hybrid (BM25 + semantic — stretch feature). Five example questions are clickable below the box.

**Outputs:** three fields — **Answer** (the grounded response with inline [n] citations), **Sources** (the document names, thread/professor titles, and URLs the answer drew from, built programmatically), and a collapsible **Retrieved chunks** panel showing the top-5 chunks with their cosine distances (or, in hybrid mode, which method(s) found each chunk), so you can see exactly what the answer is grounded in.

**Sample transcript** (one complete interaction):

```
[Your question]: Do Colby dorms have air conditioning?
[Ask]

[Answer]: One student says that air conditioners are only available in the
Johnson Pond houses [3]. However, another student mentions the cold weather,
implying that air conditioning might not be a major concern [2]. According
to one student, you'll only need an air conditioner for about two weeks
total, and a fan should suffice [3].

[Sources]:
• reddit_txeni4.txt — "Questions for Colby students / alumni :))"
  (https://www.reddit.com/r/Colby/comments/txeni4/)
• reddit_znvc3i.txt — "Banned Items at Colby Dorms?"
  (https://www.reddit.com/r/Colby/comments/znvc3i/)

[Retrieved chunks]: (collapsed by default)
[1] distance=0.253 — reddit_znvc3i.txt ...
[3] distance=0.369 — reddit_znvc3i.txt [r/Colby thread "Banned Items at
    Colby Dorms?", 2022-12] Heaters, yes. Air conditioners are in the
    Jonson pond houses only. ...
```

---

## Evaluation Report

All 5 questions from planning.md, run through the full pipeline (`python run_eval.py`; complete transcripts with all retrieved chunks are in `eval_results.md`).

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is Doghead and when does it happen? | Biggest tradition; St. Patrick's-style; weekend before spring break; all-nighter, sunrise from the library steps | All elements present, both threads cited, the "getting plastered" take attributed separately | Relevant (answer chunk rank 1, d=0.475) | Accurate |
| 2 | Can freshmen choose their dorm at Colby? | No; chem-free request only; roommate questionnaire (sleep hours, tidiness, sociability); placed in designated freshman buildings | Got "no real choice" + chem-free + accommodations nuance, but never mentioned the questionnaire or the designated freshman buildings | Partially relevant (3 of 5 chunks on target; the questionnaire and freshman-buildings chunks missed top-5) | Partially accurate |
| 3 | Do Colby dorms have air conditioning? | No, Johnson Pond houses only; bring a fan; only ~2 weeks of need; heaters yes | All core facts present and cited; one slightly stretched inference ("cold weather implies AC isn't a major concern") | Relevant (answer chunk rank 3, d=0.369; rank 1 was the question being asked in-thread) | Accurate |
| 4 | Which dining halls do students recommend for lunch vs dinner? | Lunch at Foss, dinner at Bob's; check menus; (Dana ~70% hit rate) | Got "lunch at Foss and dinner at Bob's" and the check-the-menus advice; missed the Dana hit-rate detail entirely | Partially relevant (the answer chunk barely made top-5 at rank 3, d=0.537 — above my 0.5 quality bar; two generic food-opinion chunks outranked it) | Partially accurate |
| 5 | How many on-campus Jan Plans are students expected to complete? | Three, freshman year is one of them; alternatives possible but effortful | All elements present including the internship caveat | Relevant (answer chunk rank 1, d=0.289) | Accurate |

**Score: 3 accurate, 2 partially accurate, 0 inaccurate.** The out-of-scope probe (tuition cost) correctly produced the refusal sentence with no sources.

---

## Failure Case Analysis

**Question that failed:** #2, "Can freshmen choose their dorm at Colby?" (partially accurate).

**What the system returned:** a correct general answer (minimal choice, chem-free request, accommodations) that omits two specific facts from the expected answer: the roommate-matching **questionnaire** (sleep hours, tidiness, sociability) and the **designated freshman buildings** system.

**Root cause (tied to pipeline stages):** I traced both missing facts to where their chunks actually ranked (`debug_rank.py`):

1. The freshman-buildings chunk ranks **8th** (d=0.363) — relevant, retrievable, but outside top-5. That part is a plain top-k cutoff: k=5 truncates a thread whose answer is spread across many comments.
2. The questionnaire chunk doesn't appear in the **top 40**. The chunk text is: *"im not sure if it's possible to access it now, but it's just basic things - what are your sleep hours, how tidy you are, how sociable you are..."* — it's a **reply**, and the thing it describes ("the housing form Colby uses to match roommates") only exists in the parent comment. My chunking rule treats every comment as an independent unit, so the reply lost its referent: nothing in the chunk says this is about housing, and its embedding carries almost no housing signal. This is a chunking-stage failure, not an embedding or generation one — the cleaning was fine and the LLM faithfully answered from what it was given.

**What I would change to fix it:** for reply comments, prepend a snippet of the parent comment (or the question being answered) to the chunk the same way I already prepend the thread title — context injection at chunk time. Raising k to ~8 would fix the first miss but not the second; the questionnaire chunk isn't close enough for any reasonable k.

---

## Stretch Feature: Chunking Strategy Comparison

`compare_chunking.py` builds four collections from the same documents and runs the same 5 eval queries against each. Strategies: my **semantic** chunker (without context prefixes, so the split logic is isolated), **recursive** character splitting (paragraph → sentence → word, 500 chars, 50 overlap), naive **fixed** 500-char slicing, and **semantic+prefix** (my actual production chunks). Hit = the chunk containing the known answer text appears in top-5.

| Query | Needle | semantic | recursive | fixed | semantic+prefix |
|---|---|---|---|---|---|
| Doghead | `library steps` | hit @ 1 (d=0.488) | hit @ 1 (d=0.556) | MISS | hit @ 1 (d=0.475) |
| Freshman dorm choice | `chem-free dorm` | MISS | MISS | hit @ 2 (d=0.356) | hit @ 5 (d=0.356) |
| Dorm AC | `pond houses` | MISS | hit @ 1 (d=0.425) | hit @ 1 (d=0.25) | hit @ 3 (d=0.369) |
| Dining lunch/dinner | `lunch at Foss` | hit @ 3 (d=0.368) | MISS | MISS | hit @ 3 (d=0.537) |
| JanPlan count | `3 on-campus JanPlans` | hit @ 1 (d=0.283) | hit @ 1 (d=0.337) | hit @ 1 (d=0.365) | **hit @ 1 (d=0.289)** |
| **Hits / 5** | | **3** | **3** | **3** | **5** |

**Which performed better and why:** the three bare strategies tie at 3/5, but they fail differently, and that's the interesting part. Semantic wins on precision — when it hits, its distances are the lowest (0.283–0.488), because one chunk = one person's complete thought. But its hard comment boundaries throw away conversational context: on the AC query, the answer comment ("Heaters, yes. Air conditioners are in the Jonson pond houses only...") never says "Colby" or "dorm," so without context it sinks below top-5 — while recursive and fixed accidentally rescue it by gluing the question comment to the answer comment across the boundary. Fixed wins the chem-free query the same way (the post got sliced together with surrounding housing text). The production variant — semantic splits plus a context prefix on every chunk — keeps the precision and deliberately restores the lost context, and hits 5/5. The takeaway I didn't expect: the prefix, which I originally added just for readability, is worth more than the choice of split algorithm.

---

## Stretch Feature: Hybrid Search (BM25 + Semantic)

`hybrid_search.py` runs BM25 (rank-bm25) over the same 257 chunks and fuses its ranking with the semantic ranking via **Reciprocal Rank Fusion**: each method contributes 1/(60+rank) per chunk, summed, and the fused top-5 is returned. I used RRF instead of mixing raw scores because BM25 scores and cosine distances aren't on the same scale — RRF only consumes rankings, so there's nothing to tune. In the UI, a checkbox switches modes and the chunks panel shows which method(s) found each chunk (e.g. `semantic#2, bm25#1`).

Comparison (needle = known answer text; full results in `stretch_hybrid_comparison.md`):

| Query | semantic-only | hybrid |
|---|---|---|
| Which CS professor responds to emails quickly? | hit @ rank 2 | **hit @ rank 1** |
| Is Hillside a good place to live? | hit @ rank 1 | hit @ rank 1 |
| What do students think of Professor Bender? | hit @ rank 1 | hit @ rank 1 |
| Which dining halls do students recommend for lunch vs dinner? | hit @ rank 3 | **hit @ rank 2** |

Hybrid wins or ties on all four. The improvements are exactly where I predicted in planning.md: queries with exact tokens ("emails", "Foss") that BM25 matches literally while MiniLM treats them fuzzily. On my small corpus semantic-only was already decent, so the gain is modest — but the dining query (my weakest eval case) moving from rank 3/d=0.537 to rank 2 is the kind of improvement that would matter at scale.

---

## Spec Reflection

**One way the spec helped:** writing the failure modes down before coding made debugging almost mechanical. When eval Q2 came back partially accurate, my Anticipated Challenges section already contained the hypothesis ("chunks that split key information," "single-chunk facts"), so instead of staring at a wrong answer I went straight to ranking the missing chunks (`debug_rank.py`) and found the reply-lost-its-parent problem in minutes. The spec turned "it's wrong" into "which of my two predicted failure modes is this."

**One way implementation diverged, and why:** planning.md specifies "no overlap" and pure comment-boundary chunks. In practice I added something the spec didn't have: a bracketed context prefix (thread title / professor + course) on every chunk. During Milestone 3 chunk inspection, too many chunks read like answers without questions — "It might trip your fuse..." is useless without knowing it's about dorm appliances. The prefix isn't overlap, but it's a small admission that pure isolated comments lose context; the chunking-comparison stretch results then showed it was the single highest-impact decision in the whole chunking design (3/5 → 5/5 hits). I updated my mental model: the spec's "comments are self-contained" assumption was about 80% true.

---

## AI Usage

I used Claude (Claude Code) throughout, with the planning.md spec as the contract. Three representative instances:

**Instance 1 — chunking parameters**

- *What I gave the AI:* my Chunking Strategy requirements and the corpus description (short reviews + variable-length Reddit comments), asking it to propose chunk size and overlap for semantic chunking before implementing.
- *What it produced:* a recommendation of ~800-char max chunks with 1-sentence overlap, arguing overlap insures against facts straddling boundaries.
- *What I changed or overrode:* I overrode to a 500-char cap with **no** overlap — my units are individual comments, so overlap mostly duplicates short comments, and I preferred tighter, single-opinion chunks for precision. I kept my number and accepted the documented risk; the failure case in this README is partly that tradeoff playing out, which I consider a fair price for the precision (production retrieval still hit 5/5 on the comparison set).

**Instance 2 — evaluation question design**

- *What I gave the AI:* the collected corpus digest, asking it to draft 5 specific, verifiable eval questions tied to actual chunks.
- *What it produced:* five candidates including "What do students say about Professor Dale Skrien's teaching style?" — well-grounded in the data (he has the most reviews, 16).
- *What I changed or overrode:* I rejected the Skrien question because he's no longer at Colby — nothing in the scraped reviews says that; it's knowledge I have as a student that the AI couldn't have. I swapped in the dining-halls question instead, deliberately choosing one whose answer lives in a single comment, so the eval would have a realistic chance of surfacing a retrieval failure (it did).

**Instance 3 — document collection and corpus curation**

- *What I gave the AI:* my source list (r/Colby + RMP) and the task of collecting the raw documents after direct Reddit requests came back 403 on every endpoint.
- *What it produced:* a working collection path via the PullPush archive API and RMP's GraphQL endpoint, and a candidate list of high-comment threads that included "The Waterville Secret that Everyone Knows" (21 comments — high engagement, so it scored well by the AI's selection criteria).
- *What I changed or overrode:* I cut that thread after reading the digest — the comment count was high because it's drama about a named local person, including doxxing accusations, which is both off-domain and not something I want a guide citing. Engagement metrics aren't content quality; that call needed a human reading the actual text.

---

## Repo Map

| File | What it is |
|---|---|
| `planning.md` | The spec, written before any pipeline code |
| `ingest.py` → `documents/` | Raw JSON → cleaned per-document text |
| `chunker.py` → `chunks.json` | Semantic chunking (257 chunks) |
| `embed_store.py` → `chroma_db/` | MiniLM embeddings → ChromaDB |
| `retrieve.py` | Top-k semantic retrieval with distances |
| `query.py` | Grounded generation (Groq) + programmatic attribution |
| `app.py` | Gradio UI (with hybrid-search toggle) |
| `run_eval.py` → `eval_results.md` | Evaluation runner + full transcripts |
| `compare_chunking.py` → `stretch_chunking_comparison.md` | Stretch: 4-way chunking comparison |
| `hybrid_search.py` → `stretch_hybrid_comparison.md` | Stretch: BM25 + RRF hybrid search |
| `data_raw/` | Raw collected JSON (PullPush + RMP GraphQL) |
