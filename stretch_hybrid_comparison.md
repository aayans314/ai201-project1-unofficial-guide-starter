# Hybrid search (BM25 + semantic, RRF fusion) vs semantic-only

Both methods produce a top-20 list; RRF fuses the two rankings
(score = sum of 1/(60+rank)); top-5 of the fused list is returned.

| Query | Needle | semantic-only | hybrid |
|---|---|---|---|
| Which CS professor responds to emails quickly? | `responds email quicker` | hit @ rank 2 | hit @ rank 1 |
| Is Hillside a good place to live? | `Hillside` | hit @ rank 1 | hit @ rank 1 |
| What do students think of Professor Bender? | `Bender` | hit @ rank 1 | hit @ rank 1 |
| Which dining halls do students recommend for lunch vs dinner? | `lunch at Foss` | hit @ rank 3 | hit @ rank 2 |

## Example: fused top-5 for an exact-name query

1. (semantic#2, bm25#1) `rmp_oliver_layton_2442672.txt` — [RMP review of Oliver Layton (CS231, 2019-11)] Oliver is amazing! His lectures are VERY well-organized. Plus, I've never seen any professor ...
2. (semantic#3, bm25#3) `rmp_dale_skrien_364345.txt` — [RMP review of Dale J. Skrien (CSA, 2012-03)] Dale is one of the finest professors at Colby. Endlessly kind, always available to help, and i...
3. (semantic#10, bm25#2) `rmp_allen_harper_2867220.txt` — [RMP review of Allen Harper (CS152, 2023-02)] Allen is the most enthusiastic professor you can ever have. He is super understanding and cari...
4. (semantic#5, bm25#12) `rmp_oliver_layton_2442672.txt` — [RMP review of Oliver Layton (CS151, 2019-02)] A good hire by the CS dept! Caring about students, very nice/friendly to talk to. Sometimes h...
5. (semantic#6, bm25#11) `rmp_oliver_layton_2442672.txt` — [RMP review of Oliver Layton (CS251, 2020-04)] Really nice professor. Super cool guy. He teaches really practical stuff and you will feel li...