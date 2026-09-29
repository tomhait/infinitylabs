# HotpotQA: From RAG to Multi-Agent Investigation

Answering multi-hop questions over a Wikipedia corpus with a local LLM (Llama 3.1 8B via Ollama), on a laptop, with no LLM training. The project moves through cycles (EDA, then basic RAG, improved RAG, a single agent and a multi-agent system), measuring quality, evidence, unsupported answers, LLM calls, tokens and cost, and latency at every step.

**Status:** Cycles 0–2 done. Cycle 2 (improved retrieval + RAG) raised EM from 0.383 to **0.483** with the same LLM (§4). Cycles 3–4 (agents) are next.

---

## 1. Business logic: why retrieval is the core of RAG

**The use case.** An analyst asks a question whose answer is spread across two documents, e.g. *"In what year was the university where Sergei Tokarev was a professor founded?"* Answering it takes two steps: first find *Tokarev* (who taught at Moscow State University), then find *Moscow State University* (founded 1755). The second document is never named in the question. This is **multi-hop** question answering, typical of investigations, due diligence, support and research work.

**Why RAG and not the LLM alone?** Asked closed-book, Llama 3.1 8B gets 24% exact match. With retrieved paragraphs it gets 38%. The model doesn't reliably *know* the facts, but it can *read* them. RAG also makes answers **verifiable**: every answer can point to the paragraphs it came from.

**Why retrieval is the bottleneck:**
- **The answer is extractive.** For more than 99% of non-yes/no questions, the answer appears word-for-word in a gold paragraph. If both gold paragraphs reach the LLM, answering is mostly picking the right span.
- **If a gold paragraph is missing, the LLM can't answer correctly.** It either says "unknown" or, worse, **makes up an answer** (an unsupported answer).
- **Hop 2 is the hard part.** Its title is named in the question only 14% of the time, and in 53% of bridge questions a distractor overlaps the question more than hop 2 does.

So every point of **both-gold recall** is a ceiling on answer quality, and the first thing to optimize.

### KPIs

| KPI | Business meaning | Metric |
|---|---|---|
| **Answer quality** | Is the answer right? | EM, F1 |
| **Evidence quality** | Did the system see what it needed? Can the answer be audited? | Both-gold recall@K, evidence recall@K |
| **Trust / hallucination** | How often does it answer from outside the evidence? | Unsupported-answer rate |
| **Cost** | Money per 1,000 questions | Tokens, LLM calls, estimated $ |
| **Responsiveness** | User waiting time, especially the slow tail | Latency p50 / p95 |
| **Complexity** | Engineering and maintenance burden | Components, calls per question, tuning effort |

---

## 2. Metrics and formulas

Notation: for a question $q$, $G_q$ is its set of gold paragraphs (always 2 in HotpotQA), $R_q^K$ the top-K retrieved paragraphs, and $Q$ the evaluation questions.

### Retrieval metrics (no LLM involved)

**Both-gold recall@K**, *the main retrieval metric*: the share of questions for which **all** gold paragraphs are in the top K.
$$\text{Both@}K = \frac{1}{|Q|}\sum_{q\in Q} \mathbb{1}\left[G_q \subseteq R_q^K\right]$$

**Evidence recall@K**: the share of gold paragraphs found, giving partial credit when only one of two is found.
$$\text{Recall@}K = \frac{1}{|Q|}\sum_{q\in Q} \frac{|G_q \cap R_q^K|}{|G_q|}$$

**Hop-1 / hop-2 found@K** (bridge questions): the share of questions whose hop-1 (resp. hop-2) gold paragraph is in the top K. Hop 2 is the paragraph containing the answer; ambiguous cases are excluded. This metric diagnoses *where* multi-hop retrieval breaks.

**Candidate recall**: Both@K where K is the whole candidate pool of the reranker (about 93 paragraphs). It's the ceiling for any reranker: it can't return what isn't in its pool.

### Answer metrics (official HotpotQA definitions)

Answers are normalized first: lowercase, strip punctuation and the articles *a/an/the*, collapse whitespace.

**Exact match**
$$\text{EM} = \mathbb{1}\left[\text{norm}(\hat a) = \text{norm}(a)\right]$$

**Token F1**: partial credit for overlapping words (yes/no answers must match exactly).
$$P = \frac{|\hat a \cap a|}{|\hat a|},\quad R = \frac{|\hat a \cap a|}{|a|},\quad F1 = \frac{2PR}{P+R}$$
where $\cap$ counts common tokens with multiplicity.

**Unsupported-answer rate**: the share of answers whose normalized text does *not* appear in the paragraphs given to the LLM. It's a proxy for hallucination; yes/no answers count as supported.
$$\text{Unsupported} = \frac{1}{|Q|}\sum_{q} \mathbb{1}\left[\text{norm}(\hat a_q) \not\subset \text{norm}(\text{context}_q)\right]$$

### Cost and latency

- **Tokens and calls:** prompt and completion tokens, retrieval calls and LLM calls per question.
- **Estimated cost:** $\text{cost} = (\text{prompt tokens}\times p_{in} + \text{completion tokens}\times p_{out})/10^6$. Local inference is free, so for comparability we use a hosted reference price for Llama 3.1 8B ($0.05 / $0.08 per 1M tokens).
- **Latency:** wall-clock time per question for retrieval, the LLM and the total, reported as **p50** (typical) and **p95** (slow tail: what users complain about). Rate-limit waits are tracked separately and never counted.

### Which metric matters most at each step

| Pipeline step | Primary metric | Why | Secondary |
|---|---|---|---|
| **Candidate generation** | **Candidate recall** | A gold paragraph missing here is lost for good; order doesn't matter yet | Pool size (cost of the next stage) |
| **Reranking** | **Both-gold recall@5** | The LLM sees the top 5; multi-hop needs *both* paragraphs, so a single miss already breaks the answer | Both@2 (small contexts), hop-2 found@5 (diagnosis), retrieval latency p95 |
| **Answer generation** | **EM** (headline), **F1** | EM is the official metric; F1 forgives wording differences ("Dara Torres" vs "Dara Grace Torres") | Unsupported rate: a wrong answer grounded in context is better than an invented one |
| **Whole system** | **EM at an acceptable cost and p95 latency** | The business trade-off | LLM calls per question, tokens, complexity |

**Why both-gold@5 and not recall@5?** A question with one of two gold paragraphs gets 50% recall but usually 0% answer accuracy. Both-gold matches how multi-hop answers actually succeed or fail.

---

## 3. Data and protocol

- **Dataset:** HotpotQA, *distractor* setting, validation split. Each question comes with 10 paragraphs: 2 gold and 8 distractors chosen to look relevant.
  - 80% of questions are **bridge** (find entity A, then use it to find the answer) and 20% are **comparison** (look up two named entities and compare them).
- **Pool:** 2,000 questions sampled with seed 42, and a **closed corpus of 19,260 paragraphs** (all their paragraphs, de-duplicated). One paragraph = one chunk, with its title prepended; paragraphs are short, with a median of 62 words.
- **Splits.** Test questions are never used for any decision.

| Split | Questions | Used for |
|---|---|---|
| **Test** `pool[:500]` | 500 | Every reported retrieval number |
| **Train** `pool[500:1500]` | 1,000 | Training LambdaMART |
| **Tuning** `pool[1500:2000]` | 500 | RRF weights, BM25 parameters, LambdaMART early stopping and hyperparameters |

- RAG runs use the first 300 test questions (the LLM is the slow part).

---

## 4. Results so far

### Cycle 1: baseline RAG (Llama 3.1 8B, 300 questions)

| Setup | EM | F1 | Both-gold in context | Unsupported | LLM calls | Tokens / question | Cost / 1k questions | Latency p50 / p95 |
|---|---|---|---|---|---|---|---|---|
| Closed book (100 questions) | 0.24 | 0.33 | – | – | 1 | 99 | $0.005 | 0.6 s / 1.0 s |
| BGE-small top 5 + Llama | **0.38** | **0.53** | 0.68 | 19% | 1 | 722 | $0.036 | 4.7 s / 8.4 s* |
| Contriever-MSMARCO top 5 + Llama (clean) | 0.35 | 0.46 | 0.57 | 11% | 1 | 724 | $0.036 | 3.6 s / 5.5 s |

\*Measured in an earlier session on a slower machine state. Compare latencies only between runs from the same session (§4, Cycle 2).

Retrieval gives +14 EM points. The clean Contriever-MSMARCO baseline is 3.6 EM points below BGE (not significant, p = 0.17), since it finds both gold paragraphs less often (57% vs 68%). But 32% of questions still miss a gold paragraph, mostly hop 2, which a single search can't reach.

### Cycle 2: improved retrieval (500 test questions, no LLM)

| Retriever | Both@2 | **Both@5** | Both@10 | Hop 2 @5 | Latency p50 | Trained on HotpotQA? |
|---|---|---|---|---|---|---|
| TF-IDF | – | 0.508 | – | – | ms | no |
| BM25 | – | 0.544 | – | 0.56 | ms | no |
| Contriever (unsupervised) | – | 0.470 | – | – | 33 ms | no |
| Contriever-MSMARCO | – | 0.602 | – | 0.56 | 33 ms | no |
| BGE-small-en-v1.5 | – | 0.706 | – | 0.69 | 17 ms | **yes** (train split) |
| RRF over classical lists (plain / weighted) | – | 0.544 / 0.576 | – | – | 10 ms | no |
| Classical RRF + structure (routing, slots, links) | 0.472 | 0.806 | 0.888 | 0.81 | 10 ms | no |
| Contriever-MSMARCO + slots + links | 0.506 | 0.836 | 0.900 | 0.82 | 48 ms | no |
| BGE + slots + links | 0.540 | 0.842 | 0.916 | 0.86 | 27 ms | yes |
| **LambdaMART, classical features** | 0.710 | 0.898 | 0.936 | 0.91 | 16 ms | no |
| LambdaMART + BGE | 0.756 | 0.920 | 0.964 | 0.92 | 35 ms | yes |
| **LambdaMART + Contriever-MSMARCO (selected)** | 0.744 | **0.924** | 0.962 | **0.93** | 59 ms | **no** |

**Main lessons:**
1. **Following links is the key multi-hop ingredient.** It adds 14–23 points to any first-stage retriever: read the top hop-1 paragraphs, then retrieve the paragraphs whose titles they mention.
2. **Merging lists with RRF alone barely beats BM25** (0.576 vs 0.544). Structure (question routing, reserved slots, links) is what brought the classical ranker to 0.806.
3. **A learned combiner beats hand-tuned rules by a wide margin:** LambdaMART goes from 0.806 to 0.898 on the same classical signals. It wins 48 questions and loses 2 (sign test p ≈ 2e-12), and both-gold@2 rises from 0.47 to 0.71.
4. **BGE's advantage is likely in-domain training.** BAAI lists HotpotQA (train split) in BGE's fine-tuning data. BGE leads the clean Contriever-MSMARCO by 10 points as a single search, but the gap disappears once links or LambdaMART are added (0.920 vs 0.924).

### Cycle 2: improved RAG end to end (Llama 3.1 8B, same 300 questions and prompt as Cycle 1)

Only the retriever changes. The **oracle** gives the LLM exactly the 2 gold paragraphs: it isn't a real system, but it shows the ceiling of this LLM with perfect retrieval.

| Run | EM | F1 | Both gold in context | Retrieval / reasoning failures | Unsupported | Prompt tokens | Latency p50 / p95 | Cost / 1k |
|---|---|---|---|---|---|---|---|---|
| Cycle 1: BGE | 0.383 | 0.527 | 68% | 24% / 20% | 18.7% | 716 | (earlier session) | $0.036 |
| Cycle 1: Contriever-MSMARCO | 0.347 | 0.462 | 57% | 33% / 20% | 10.7% | 719 | 3.6 s / 5.5 s | $0.036 |
| LTR classical | 0.457 | 0.606 | 89% | 8% / 28% | 5.3% | 646 | 3.3 s / 4.7 s | $0.033 |
| **LTR + Contriever (selected)** | **0.483** | **0.636** | **91%** | **5% / 29%** | **6.0%** | 647 | **3.9 s / 5.7 s** | $0.033 |
| Oracle (gold only) | 0.577 | 0.736 | 100% | 0% / 22% | 3.3% | 307 | 1.3 s / 2.0 s | $0.016 |

- **+10 EM points over BGE from retrieval alone,** significant: 43 questions won vs 13 lost (p < 0.001), 95% CI for ΔEM [+0.05, +0.15]. The gain is on bridge questions (EM 0.37 → 0.48).
- **+13.7 EM points over the clean baseline** with the same dense model: Contriever-MSMARCO as a single search gets 0.347, and inside LTR it gets 0.483 (56 won vs 15 lost). This is the cleanest measure of what Cycle 2 adds.
- **Half of the gap to perfect retrieval is closed** (0.383 → 0.483 of 0.577).
- **The bottleneck moved from retrieval to the LLM.** Retrieval failures dropped from 24% to 5%, while reasoning failures rose from 20% to 29%: the same questions now reach the LLM with full evidence, and it answers about 50% of those correctly, as before. Even with perfect retrieval, the 8B model misses 42% by EM.
- **Distractors still hurt:** with full evidence, 5 paragraphs give EM 0.50 vs 0.56 with only the 2 gold ones.
- **More grounded:** unsupported answers dropped from 18.7% to 6.0%, and abstentions from 8.3% to 1.3%.
- **Nearly free in latency and cost.** Compared within the same session, LTR + Contriever takes 3.9 s p50 / 5.7 s p95 vs 3.6 s / 5.5 s for the single Contriever search (+0.3 s / +0.2 s). The classical LTR is the fastest real system (3.3 s / 4.7 s). Prompts are slightly shorter because LTR picks shorter paragraphs, so the cost per question drops a little.

---

## 5. The selected model: LambdaMART reranker + Contriever-MSMARCO

**Why this one:**
- **Best evidence and best answers:** 0.924 both-gold@5, 0.962 @10, and hop 2 found 93% of the time. End to end: EM 0.483 / F1 0.636 vs 0.383 / 0.527 for Cycle 1.
- **Contamination-free:** Contriever-MSMARCO was trained on MS MARCO only. LambdaMART was trained on 1,000 of our pool questions, separate from the test questions and fully visible.
- **Small latency cost:** 50–60 ms of retrieval standalone. End to end, +0.3 s p50 vs a single Contriever search in the same session (3.9 s vs 3.6 s), for +13.7 EM points.
- **Cheap to train:** about 1 s on a laptop, and 100 questions already give 0.884.

**Fallback:** *LambdaMART with classical features only* (0.898, 16 ms, no neural model, fully explainable). It's the natural low-cost option in the final comparison.

The pipeline has two stages: **candidate generation** (cheap signals build a wide pool, judged by candidate recall) and **reranking** (the learned ranker orders the pool, judged by both-gold recall@5). Both stages are measured with recall; what differs is the cutoff: the whole pool (~93) versus the 5 paragraphs the LLM reads.

```
question ──► signal lists (BM25, TF-IDF, title, coverage, answer type, Contriever)
         ──► structured RRF + link following (hop 1 → hop 2)
         ──► candidate pool (union, ~93 paragraphs)            ← candidate generation
         ──► 33 features per (question, paragraph)
         ──► LambdaMART score → sort → top 5 to the LLM         ← reranking
```

### 5.1 Signals (all computed per question)

| Signal | What it measures |
|---|---|
| `bm25` | BM25 over stemmed unigrams (k1 = 1.2, b = 0.9) |
| `tfidf` | TF-IDF cosine similarity over unigrams and bigrams |
| `title` | Question entities matching a paragraph's **title**: exact 1.0, partial 0.7, fuzzy (character-trigram Dice ≥ 0.75), weighted by entity rarity (IDF) |
| `coverage` | Rarity-weighted share of question entities mentioned in the paragraph (first sentence 1.0, body 0.6) |
| `anstype` | The paragraph contains an entity of the expected answer type (a DATE for "what year"…) |
| `dense` | Contriever-MSMARCO dot-product similarity, a frozen model with paragraph embeddings cached |
| **Links** | A paragraph *links* to another if it mentions that paragraph's title or an alias (title gazetteer: a classical stand-in for Wikipedia hyperlinks) |

**Question entities** come from four sources: spaCy NER, a title gazetteer (question n-grams that equal a corpus title), quoted strings, and capitalized runs.

**Routing rule:** a question is treated as comparison-like when it has at least 2 named entities and either a yes/no opener or a comparison cue ("older", "both", "same"…). This agrees with HotpotQA's own labels 90% of the time.

### 5.2 Candidate generation

Candidates are the **union of the top 50 of every ranked list**, duplicates removed:
- **Structured RRF ranking:** weighted RRF, $\text{RRF}(d)=\sum_i \lambda_i/(60+\text{rank}_i(d))$, with routing, reserved slots and link-following.
- **Reserved slots:** the best paragraph for each named entity that exactly matches a title.
- **Each signal list:** BM25, TF-IDF, title, coverage, answer type, Contriever.
- **Bridge and comparison RRF rankings:** the hop-1 rankings.
- **Forward-link candidates:** paragraphs mentioned by the top-5 hop-1 paragraphs. A candidate reached from the hop-1 paragraph at rank $r$ scores $0.5^{r-1}\big(1+\text{ov}(\text{linking sentence})+\text{ov}(\text{candidate's first sentence})\big)$, where ov is the summed IDF of the question words outside the entities that the text contains.
- **Backlink candidates:** paragraphs that mention a top-5 hop-1 paragraph.

**Result:** 54–171 candidates per question (mean 93). Both gold paragraphs are in the pool for **99.2%** of test questions.

Measured on 300 test questions, the structured-RRF top 50 alone already contains 99% of the gold paragraphs. The other sources rarely add new golds; their value is **information**, since each list's scores and ranks become features. They also provide realistic **hard negatives** for training, such as same-name look-alikes and near-miss BM25 matches.

### 5.3 Features (33 per candidate)

| Group | Features |
|---|---|
| Question | `is_comparison`, `n_entities`, `n_named`, `question_len`, `has_anstype` |
| Lexical | `bm25`, `bm25_rel` (÷ max for the question), `bm25_rank`, `tfidf`, `tfidf_rel`, `tfidf_rank` |
| Dense | `dense`, `dense_gap` (question's best score − this score), `dense_rank` |
| Entity | `title_score`, `title_rank`, `is_slot`, `coverage`, `coverage_rank`, `anstype` |
| RRF | `bridge_rrf_rank`, `comparison_rrf_rank`, `structured_rank` |
| Link | `fwd_score`, `fwd_rank`, `fwd_parent_rank` (rank of the best hop-1 paragraph linking to it), `fwd_parent_count`, `back_score`, `back_rank`, `back_parent_rank` |
| Paragraph | `first_sentence_overlap`, `title_in_question`, `paragraph_len` |

A paragraph absent from a list gets a **missing** rank, which the trees handle natively.

### 5.4 Reranking with LambdaMART

**The model:** LightGBM `LGBMRanker` with `objective="lambdarank"`, an ensemble of small gradient-boosted decision trees.

**Training:**
- Each question is a **group** of about 93 rows (candidates × features). Label 1 = gold paragraph, 0 = other.
- On each boosting round, for every (gold, non-gold) pair *within a question*, the gradient pushes the gold paragraph up. The push is weighted by $|\Delta \text{NDCG@5}|$, the change in NDCG@5 if the two swapped, so errors near the top count most.
- Settings:
  - learning rate 0.05
  - rows subsampled at 80% and features at 80% per tree
  - up to 1,000 trees, with **early stopping** on validation NDCG@5 (patience 50)
- **Hyperparameters:** a 6-point grid (`num_leaves` ∈ {7, 15, 31} × `min_child_samples` ∈ {20, 50}), selected on validation both-gold@5. All six points land within 0.006 of each other, so the model isn't sensitive to them. The selected Contriever model has 15 leaves, minimum leaf size 50, and 245 trees.

**Scoring at query time:**
- Each candidate goes through every tree; each tree ends in a leaf value, and **score = sum of the leaf values**.
- Candidates are sorted by score and the top 5 go to the LLM.
- Scores only mean something *within* a question.
- Model inference takes about 0.6 ms per question; the rest of the latency is feature extraction.

**How Contriever enters the model:**
1. Its top 50 is a candidate source.
2. `dense`, `dense_gap` and `dense_rank` are direct features.
3. Its list is fused into the structured RRF (weight 2), which shapes the hop-1 ranking, which links get followed, and the RRF features.

Contriever itself is never fine-tuned. The GBM learns *when* to trust its scores.

### 5.5 What the model relies on

| Analysis | Finding |
|---|---|
| **Ablation** (retrain without a feature group, classical model) | Links −0.028 (the only group it can't do without); entity −0.010; lexical −0.008; question −0.002; paragraph 0.000; RRF features +0.004 (not needed: the trees rebuild them from raw features) |
| **Gain importance** | `structured_rank` takes about 68% of the gain, but the ablation shows it isn't necessary. Importance shows what the model split on, not what it needs |
| **Learning curve** | 100 training questions: 0.884; 1,000: 0.898. The gain comes from the model's flexibility, not from data volume |
| **Failures fixed vs RRF + structure** | "Only a backlink" 11/16, "link outranked" 4/5, "hop 1 missed" 14/25, "no link in either direction" 8/27 |

### 5.6 Leakage checks (a 9-point jump deserves suspicion)

- **No preference for "gold-looking" paragraphs:** 10% of LambdaMART's wrong top-5 picks are gold for *another* question, versus 14% for RRF (20% of the corpus is gold for some question).
- **Validation and test agree:** 0.880 vs 0.898 for the classical model.
- **One mild corpus artifact:** gold paragraphs are shorter than HotpotQA's TF-IDF-chosen distractors. Length alone reaches 0.13 both@5 (random ordering: about 0.002), but removing the paragraph features doesn't change the score.

---

## 6. Rejected technologies (and why)

| Technology | Result | Reason rejected |
|---|---|---|
| **Plain / weighted RRF** as the final ranker | 0.544 / 0.576 | Ranks only, with no confidence or interactions; barely beats BM25 |
| **Always-on backlinks** | Coverage 65% → 84%, but both@5 unchanged or worse | Backlink candidates push correct forward links out of the top 5; only a learned model can decide when to trust them |
| **Stemming / lemmatization for title matching** | +0.7 points of link coverage | Word-level matching tops out at about 70% coverage; the misses are paraphrases, not inflections |
| **Word-vector (GloVe) soft title matching** | About +2% coverage | Noisy matches, a 480 MB dependency |
| **Title aliases** (comma head, acronyms) | +0.002 when removed | Rarely triggered, and some added links are wrong |
| **BGE as the main retriever** | Best single-search retriever (0.706) | Trained on the HotpotQA train split: an unfair, in-domain advantage. BGE-large has the same training data |
| **Unsupervised Contriever** | 0.470 | Weaker than BM25 without MS MARCO fine-tuning |

---

## 7. Caveats

- **Closed corpus.** 19,260 paragraphs built from the pool's contexts. The title gazetteer (our stand-in for hyperlinks) would find many spurious links against full Wikipedia (about 5M titles); in an open setting, use real hyperlinks.
- **Supervision.** LambdaMART learns from gold labels on 1,000 HotpotQA questions. That's the same *kind* of in-domain supervision we flagged for BGE, just much smaller, visible, and on separate questions.
- **Noise level.** On 500 questions, one question = 0.2 points; differences under about 2 points are within noise.
- **RAG sample size.** 300 questions (47 comparison questions, so one comparison question ≈ 2 points). Per-type differences between retrievers on comparison questions are within noise.
- **Shorter-paragraph bias.** Part of the prompt-token and latency saving comes from LTR preferring shorter paragraphs, a corpus artifact (gold paragraphs are shorter than HotpotQA's distractors) that wouldn't necessarily hold on another corpus.
- **Hybrid RRF weights** inside the feature pipeline were tuned with BGE and reused for Contriever. LambdaMART can reweight the raw features, so the effect is small.

---

## 8. Next steps

1. **Cycle 3, single agent.** The bar to beat is EM 0.483 at 1 LLM call and about 4 s. Since retrieval failures are down to 5%, the agent must mainly **reason better**: decompose the question, check the answer type ("which aired first" wants a title, not a date), verify the answer against the evidence, and write a follow-up query only when evidence is missing. The same LTR ranker serves as its search tool.
2. **Cycle 4, multi-agent**, then the final comparison across quality, evidence, unsupported answers, calls, tokens and cost, latency and complexity.

---

## 9. Reproducing

**Environment**
- Python 3.14 virtual environment in `.venv`.
- Ollama running `llama3.1` locally (for the RAG cycles).
- In VS Code, choose the Jupyter kernel **"hotpotQA (.venv, Python 3.14)"**.
- `.env` holds API keys, is git-ignored and must never be committed.

```bash
source .venv/bin/activate
python -m src.rag retrieval --retriever contriever_msmarco   # Cycle 1 single-search retrievers (also: dense, contriever, bm25, tfidf)
python -m src.rag rag --n 300                                # Cycle 1 RAG with Llama
python -m src.fusion                                         # Cycle 2 classical RRF rankers + ablations
python -m src.fusion --dense                                 # Cycle 2 dense + links, hybrid
python -m src.ltr                                            # Cycle 2 LambdaMART: 3 variants, ablation, learning curve (~6 min)
python -m src.rag rag --n 300 --retriever ltr_hybrid_contriever_msmarco   # Cycle 2 RAG (also: ltr_classical, oracle; ~20 min each)
```

Notes:
- LightGBM and PyTorch clash on macOS (their OpenMP runtimes deadlock or segfault). Training uses `n_jobs=1`. To load a saved model, `load_ltr_retriever` sets `OMP_NUM_THREADS=1` and must run before PyTorch is imported; retrieval latency is unaffected.
- For offline runs with cached models, set `HF_HUB_OFFLINE=1`.

### Project layout

| Path | Contents |
|---|---|
| `src/data.py` | Dataset loading, fixed pool, corpus, hop labels |
| `src/classical.py` | BM25, TF-IDF |
| `src/retrievers.py` | Dense retrievers (BGE, Contriever, Contriever-MSMARCO) |
| `src/entities.py` | Question entities, title gazetteer, aliases, links, backlinks, fuzzy titles |
| `src/fusion.py` | RRF, structured ranker (routing, slots, links) |
| `src/ltr.py` | LambdaMART: candidates, features, training, retriever |
| `src/rag.py`, `src/llm.py`, `src/evaluate.py` | RAG pipeline, LLM client (Ollama/Groq, cached), metrics |
| `notebooks/00_eda`, `01_baseline_rag`, `02_classical_ranking`, `03_improved_rag` | Analyses with findings (`.py` sources, `.ipynb` executed) |
| `results/` | Per-question JSONL for every run, summary CSVs, figures |
| `cache/` | Embeddings, entity/link indexes, LTR features and models, LLM responses |
