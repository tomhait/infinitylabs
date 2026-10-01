# Final presentation and defense questions

[← Overview](../README.md) · [EDA](01_eda.md) · [Candidates and reranking](02_candidates_and_reranking.md) · [Answer extraction](03_answer_extraction.md) · **Final presentation**

This document covers the assignment's **"Final presentation"** section and the **"Questions you must be able to answer"**. The slide deck is [`presentation.html`](presentation.html) (open in a browser; arrow keys to navigate, `P` to print to PDF). All numbers are on the 300 test questions unless marked "dev".

**Research question:** *when does iterative or multi-agent investigation provide enough benefit over conventional RAG to justify the extra cost and complexity?*

**Short answer:** rarely, in this setting. Better retrieval (+10 EM) and a cheap rule-checked agent (+3.4 EM at the same latency) are worth it. Iterative retrieval fixes retrieval but not answers (EM 0.533 vs 0.537), and the multi-agent team (+4.3 EM over the single agent, significant) only matches a bigger model used in the single agent, at 5× the calls and 3.5× the latency.

---

## 1. Talk outline (15–20 minutes)

| # | Section (assignment order) | Minutes | Key message | Material |
|---|---|---|---|---|
| 1 | **Problem** | 1 | Multi-hop investigation: the second document is never named in the question | [Overview §1](../README.md#1-business-logic-why-retrieval-is-the-core-of-rag) |
| 2 | **Dataset** | 2 | HotpotQA distractor, 2,000 questions, closed corpus of 19,260 paragraphs; hop 2 named in the question only 14% of the time | [EDA](01_eda.md) |
| 3 | **Baseline** | 1.5 | Cycle 1: BGE top 5 + Llama 8B, EM 0.383; RAG beats closed book (0.24) | [Answer extraction](03_answer_extraction.md#cycle-1-basic-rag) |
| 4 | **Evaluation** | 1.5 | KPIs; both-gold recall@K as the retrieval KPI; EM/F1, unsupported rate, calls, cost, p50/p95 latency; splits; sign tests | [Overview §2–3](../README.md#2-metrics-and-formulas) |
| 5 | **Failure analysis** | 1.5 | 32% miss a gold paragraph, mostly hop 2 → follow links | [Retrieval](02_candidates_and_reranking.md#cycle-1-a-single-search) |
| 6 | **Improved pipeline** | 3 | Candidates + LambdaMART: both@5 0.706 → 0.924, EM 0.483; sentence reranker: same quality at half the tokens and latency | [Retrieval](02_candidates_and_reranking.md#cycle-2-candidate-generation--lambdamart-reranking) |
| 7 | **Single agent** | 2.5 | Checked agent 0.537 (13 / 3 vs Cycle 2c); iterative decomposed agent fixes retrieval but not answers | [Answer extraction](03_answer_extraction.md#cycle-3-a-single-agent-langgraph) |
| 8 | **Multi-agent** | 2.5 | Team with a 14B judge: 0.580, significant over every Llama system, but equal to Qwen 14B alone | [Answer extraction](03_answer_extraction.md#cycle-4-a-multi-agent-investigation-team-langgraph) |
| 9 | **Comparison** + the 5 cases | 3 | The mandatory table; one example per required case | §2–3 below |
| 10 | **What I would deploy and why** | 1 | Checked agent on Llama 8B; Qwen 14B in the same agent if accuracy is worth 8× the cost | §5 below |
| – | What I would NOT use | (within 9) | Two or more rejected technologies with reasons | §4 below |

---

## 2. Mandatory final comparison

| Metric | Baseline (Cycle 1: BGE top 5) | Improved pipeline (Cycle 2c: LTR + sentences) | Single agent (Cycle 3: checked) | Single agent, iterative (Cycle 3: decomposed) | Multi-agent (Cycle 4: team, 14B judge) |
|---|---|---|---|---|---|
| **Main quality metric** (EM / F1) | 0.383 / 0.527 | 0.503 / 0.654 | **0.537 / 0.676** | 0.533 / 0.686 | **0.580 / 0.719** |
| **Evidence quality** (both gold in the LLM's context) | 68% | 80% | 84% | **94%** | 87% |
| **Unsupported answers** | 18.7% | 6.0% | 3.0% | **2.3%** | 3.3% |
| **Avg retrieval calls** | 1 | 1 | 1 | 3.2 | 4.2 |
| **Avg LLM calls** | 1 | 1 | 1.11 | 4.24 | 5.96 |
| **Prompt tokens / cost per 1k questions** | 716 / $0.036 | **281 / $0.014** | 357 / $0.018 | 1,438 / $0.076 | 2,213 / $0.254 |
| **Latency p50 / p95** (clean benchmark) | 3.0 s / 4.4 s | **1.5 s / 2.0 s** | 1.6 s / 4.1 s | 6.6 s / 10.0 s | 9.5 s / 32.6 s |
| **Complexity / debuggability** | 1 component; trivial | 2 trained rankers + feature pipeline; every stage measured offline | + 2 rule steps, ≤ 2 LLM calls; every decision logged | Plan + up to 3 hops + synthesis; errors propagate from hop 1, harder to trace | 2 agents + consensus + judge, 2 models, memory swapping; most moving parts |

Significance (sign test): improved vs baseline 43 / 13 (p < 0.001, paragraph version); single agent vs improved 13 / 3 (p = 0.02); team vs single agent 16 / 3 (p = 0.004); team vs Qwen 14B alone 26 / 24 (p = 0.89).

---

## 3. The five required cases

### 3.1 A baseline failure fixed later (retrieval: the missing hop 2)

> *"The Distribution of Industry act was passed by a man who was prime minister when?"* Gold: **1945 to 1951**

| System | Answer | Why |
|---|---|---|
| Cycle 1 (BGE) | **1868–74** ✗ | Retrieved the act and a *distractor* prime minister (William Ewart Gladstone), but not **Clement Attlee**, the hop-2 paragraph. Llama answered from the wrong prime minister: a retrieval failure that produced a confident wrong answer |
| Cycle 2 onward | **1945 to 1951** ✓ | The act's paragraph mentions Attlee; **link following** pulls in the Attlee paragraph and LambdaMART ranks it into the top 5. Correct in every later system |

This is the most common Cycle 1 failure (retrieval failures 24% → 5% in Cycle 2).

### 3.2 A remaining failure (reasoning, even with perfect evidence)

> *"Which film director is younger, Robert Z. Leonard or Sinclair Hill?"* Gold: **Sinclair Hill**

Evidence (both gold paragraphs retrieved): *Robert Zigler Leonard (October 7, 1889 – …)*; *Sinclair Hill (1894–1945)*.

Every system answers **Robert Z. Leonard**: Cycle 2, both Cycle 3 agents, Qwen 14B, the team, and even the oracle with only the two gold paragraphs. The model must compare two birth years and map "younger" to "born later"; it doesn't. Retrieval is perfect; the error is reasoning.

34 test questions are wrong in every system. Besides reasoning errors like this one, many are **wording mismatches** that EM counts as wrong: "Bobby Hurley" for *Robert Matthew Hurley*, "729" for *729 at the 2010 census*, "C. J. Cherryh" for a gold answer that copies a whole sentence. F1 gives these partial credit.

### 3.3 A case where an agent helped (the checked agent's type check + repair)

> *"The 249th episode of "The Simpsons" was aired on what date?"* Gold: **November 1, 2000**

| Step | Output |
|---|---|
| Cycle 2c draft (5 selected sentences) | **Treehouse of Horror XI** ✗ (the episode's name, not its date) |
| Check (no LLM) | `expects_date`: the question asks "what date" but the answer has no date |
| Repair (LLM call 2, whole paragraphs, told why) | **November 1, 2000** ✓ |

Same pattern: *"Who created the NBC sitcom that Johnny Pemberton appears in as Bo Thompson?"* The sentence selector dropped the answer sentence, the draft abstained ("No answer found"), the `abstained` check fired, and the repair reread the whole paragraphs → **Justin Spitzer** ✓. The checks flag 13% of answers; on test the agent wins 13 questions and loses 3 vs Cycle 2c.

### 3.4 A case where the agent was unnecessary (iterative retrieval on an easy question)

> *"In what year was the university where Sergei Aleksandrovich Tokarev was a professor founded?"* Gold: **1755**

- **Cycle 2c, 1 LLM call:** the top 5 sentences already contain both facts → **1755** ✓.
- **Decomposed agent, 4 LLM calls, 3 retrievals:** "What university was Tokarev a professor at?" → *Moscow State University*; "In what year was Moscow State University founded?" → *1755*; synthesis → **1755** ✓. Same answer at 4× the calls and about 4× the latency.

This isn't rare: on **66 of the 151** questions Cycle 2c already answers correctly, the decomposed agent spends 4 or more calls to reach the same answer. It always runs its full plan (it has no "enough evidence already?" exit), so it over-searches on easy questions.

### 3.5 A case where multi-agent failed

> *"Repertoire of Plácido Domingo appeared in an opera written by whom which was based on a play by William Shakespeare?"* Gold: **Giuseppe Verdi**

| Agent | Answer |
|---|---|
| Direct investigator (checked agent) | **Giuseppe Verdi** ✓ |
| Chain investigator (decomposed) | hop 1: "the opera … based on a play by Shakespeare" → *The Enchanted Island* (a wrong bridge entity); hop 2 → **Jeremy Sams** ✗ |
| Qwen 14B judge, both orders | picks the chain answer both times → team answers **Jeremy Sams** ✗ |
| Qwen 14B alone (single checked agent) | **Giuseppe Verdi** ✓, 1 call |

The team spent 7 LLM calls and 27 s to turn a right answer into a wrong one. In aggregate the multi-agent structure added little: the team and Qwen 14B alone are 26 / 24 on test. Another failure mode: when the judge's two orders disagree (24 of 92 disagreements), it falls back to the direct answer; on *"Douglas D. Scott … the site of a battle that occurred in what year?"* that discarded the chain's correct **1876** (Little Bighorn) for "mid-1980s".

---

## 4. What I would NOT use

| Rejected | Evidence | Why |
|---|---|---|
| **Free-form ReAct agent** (the LLM chooses tools, queries and when to stop) | Not built | An 8B model is unreliable at planning tool calls and judging "enough evidence"; a fixed LangGraph flow with deterministic checks is predictable, bounded and measurable per step |
| **BGE as the main retriever** | Best single search (0.706 both@5) | Fine-tuned on the HotpotQA train split: an in-domain advantage that disappears inside LambdaMART (0.920 vs 0.924 for the clean Contriever-MSMARCO) |
| **Plain / weighted RRF as the final ranker** | 0.544 / 0.576 | Barely beats BM25; LambdaMART on the same signals reaches 0.898 (48 won / 2 lost) |
| **Self-consistency** (5 samples, majority vote) | 0.527 vs 0.537, 4.6× calls | Samples from one model share its mistakes; diversity must come from different strategies or models |
| **An 8B judge** | Dev 0.600 (n.s.), test 0.563 | Position bias (picks the first answer shown in both orders in 35 of 91 dev cases) and leniency; a verifier must be stronger than the workers |
| **Decomposition as the main agent** | 0.533 vs 0.537 at 4× calls | A wrong hop-1 answer propagates; kept only as the second investigator |
| **Full Wikipedia index** | – | Beyond a laptop budget; a closed corpus keeps the research question |

More: [retrieval](02_candidates_and_reranking.md#rejected-retrieval-technologies), [answer extraction](03_answer_extraction.md#rejected-answer-extraction-technologies).

---

## 5. What I would deploy and why

**The Cycle 3 checked agent on Llama 3.1 8B, on the Cycle 2 / 2c retrieval stack:** EM 0.537, 3% unsupported, 1.1 LLM calls, $0.018 per 1,000 questions, 1.6 s median / 4.1 s p95. It is RAG plus two deterministic steps and an occasional second call: almost the operational profile of plain RAG, significantly better answers, and every decision is logged.

- **If accuracy matters more than cost:** the same agent with Qwen 14B (0.573, 2.7 s / 8.0 s, 8× the cost); not the team, which matches it at 5× the calls and 3.5× the median latency.
- **The team** only where a strong model can't serve every question but a stronger verifier can be called on the 30% of disagreements (a hosted judge, or batch investigations).

---

## 6. Questions you must be able to answer

### Why RAG? Why not a direct LLM?

- **The model doesn't know the facts, but it can read them.** Closed book: EM 0.24; with retrieved paragraphs: 0.37 on the same 100 questions (bridge questions 0.20 → 0.35). The final system reaches 0.537.
- **Closed-book answers are confident inventions:** "1880" for Moscow State University's founding (correct: 1755).
- **Verifiability:** with RAG every answer points to its evidence; 97% of the checked agent's answers appear in the evidence it read (3% unsupported). An investigation assistant must show its sources.
- **Freshness and scope:** the corpus can be updated or restricted (private documents) without retraining, and no LLM training is allowed here anyway.

### Why this retriever and Top-K?

- **Chunk = one paragraph with its title** (EDA: paragraphs are short, median 62 words for gold, and self-contained; splitting would separate facts from the entity they describe).
- **K = 5 is the knee of the recall curve:** both-gold recall 46% at K = 2, 71% at K = 5, only +9 points at K = 10 for twice the tokens and more distractors (which cost about 6 EM points even with full evidence).
- **Retriever: LambdaMART over link-aware candidates with Contriever-MSMARCO:** the best both@5 (0.924, hop 2 found 93%), contamination-free (Contriever-MSMARCO never saw HotpotQA; LambdaMART trained on 1,000 separate questions), 59 ms, trains in about 1 s.
- **Then top 5 sentences, not paragraphs, to the LLM:** same quality, 57% fewer tokens, half the latency.

### When does BM25 beat dense retrieval?

- **BM25 (lexical)** scores exact term overlap weighted by rarity (IDF) with length normalization. It wins when the query and document share **rare exact strings**: names, titles, numbers, codes, jargon the embedding model never saw. It needs no training and is robust out of domain.
- **Dense (semantic)** embeds query and document separately (bi-encoder) and wins on **paraphrases and indirect descriptions** ("the university where X was a professor"), where the words differ.
- **In this project:** BM25 (0.544 both@5) beats unsupervised Contriever (0.470), i.e. a dense model without relevance training, but loses to Contriever-MSMARCO (0.602) and BGE (0.706). Comparison questions always name both entities, which favors lexical and title matching; their tuned RRF weights rely on TF-IDF and title match, while the bridge weights give BM25 weight 2.
- **Best of both: hybrid.** Both signals go into the candidate pool and the LambdaMART features; removing the lexical features costs 0.008 both@5, and the reranker decides per question which signal to trust.

### Why rerank?

- **Retrieval has two jobs with different trade-offs.** Candidate generation must be cheap and wide (99.2% of questions have both gold paragraphs in the ~93-candidate pool). The LLM reads only 5, so the *order* of those candidates decides the answer.
- **A reranker can afford rich features on a small pool:** 33 features per candidate (lexical, dense, entity, link, structural), combined by a learned model. On the same signals, hand-tuned RRF reaches 0.806 both@5 and LambdaMART 0.898 (48 won / 2 lost); both@2 jumps from 0.47 to 0.71.
- **Bi-encoder vs cross-encoder:** a bi-encoder encodes query and document separately (fast, pre-computable, used for search); a cross-encoder reads them together (more accurate, but one model pass per pair, so only for reranking a short list). Our reranker is a feature-based LambdaMART instead: it can use cross-paragraph signals (which paragraph links to which) that a pairwise cross-encoder can't see, in 0.6 ms of inference.
- **Sentence reranking** applies the same idea one level down: a second LambdaMART keeps the 5 best sentences.

### Why did improved RAG still fail?

- **The bottleneck moved from retrieval to the LLM.** Retrieval failures dropped from 24% to 5%, reasoning failures rose from 20% to 29%. With perfect retrieval (the oracle) Llama 8B still misses 42% by EM.
- **Distractors still hurt:** with full evidence, 5 paragraphs give 0.50 vs 0.56 with only the 2 gold ones.
- **Sentence selection drops evidence for 25% of questions:** EM 0.289 there vs 0.576 when all support is kept.
- **Typical reasoning errors:** answering the wrong hop or the wrong type ("what county" answered with a town), comparisons and date arithmetic (the Leonard vs Hill case), and format mismatches EM punishes ("May 1, 1989" for "what year"). These motivated the Cycle 3 checks.

### What exactly makes the system an agent?

The assignment's definition: **the next retrieval action or query depends on intermediate evidence observed at runtime.**
- **Decomposed agent (iterative retrieval):** the hop-2 query doesn't exist until hop 1 is answered. For Tokarev, it first asks "What university was Tokarev a professor at?", observes *Moscow State University*, then builds and runs a new search, "In what year was Moscow State University founded?". It averages 3.2 retrievals per question.
- **Checked agent:** its control flow depends on runtime observations of its own output: deterministic checks inspect the draft and, if it fails (13%), route to a repair step that reads different evidence (the whole paragraphs) with feedback on what was wrong.
- **What it is not:** a free-form ReAct loop where the LLM decides "enough evidence?" after each search. Our agents plan their hops up front (2–3 sub-questions) and use deterministic sufficiency checks instead of LLM self-assessment, deliberately: an 8B model judges its own evidence poorly, and a fixed graph is bounded and debuggable. The cost of that choice is visible in case 3.4: no early exit when the first retrieval was already enough.

### Why multi-agent instead of one agent with multiple tools?

- **Independence and diversity.** One agent with more tools still follows one line of reasoning and anchors on its own earlier steps. Two investigators with *different strategies* fail on different questions: they agree on 70% (EM 0.72 there) and disagree on 30%, where picking the right one would lift EM to 0.673 (dev).
- **Separation of roles:** the investigators produce answers; the judge only verifies, with a clean context that contains both answers and their evidence but none of the investigators' intermediate mistakes.
- **Different models per role:** the expensive 14B model is used only as the judge, on the 30% of disagreements.
- **The honest result:** the structure works (team 0.580 vs 0.537, p = 0.004; vs self-consistency 24 / 8) but doesn't beat **one agent with the bigger model** (0.573; 26 / 24). In this setting the gain came from model capacity, not from the multi-agent structure.

### How do you stop loops and debug decisions?

- **Loops are impossible by construction.** Each agent is a LangGraph graph with a fixed shape: the only cycle is the hop loop, capped at 3 sub-questions; repair runs at most once; the judge makes exactly 2 calls. Hard upper bounds, all reached on test: 2 LLM calls for the checked agent, 6 for the decomposed agent (decompose + 3 hops + synthesis + repair), 10 for the team (2 + 6 + 2 judge calls).
- **No unbounded LLM decisions:** stopping and routing are decided by code (checks, consensus, the order-swap rule), not by the LLM.
- **Every decision is logged per question** in the results JSONL: the draft, which checks failed, the format rules applied, whether repair ran and what it returned, the sub-questions and each hop's answer, both investigators' answers, the judge's picks in both orders and whether it decided.
- **Reproducible:** temperature 0 and a disk cache of every LLM call replay a run exactly; the stored drafts give the ablation (draft → trim → checks) from a single run.
- **Measured per step:** calls, tokens, retrieval and LLM latency per question; failure classes (retrieval vs reasoning) per system.

### When would you deploy normal RAG instead?

- **When questions are single-hop** or the evidence sits in one document: one retrieval finds it, and an agent only adds latency.
- **When retrieval already brings both documents:** comparison questions name both entities (both@5 99% already in Cycle 1); agents add little there.
- **Under strict latency or cost budgets:** Cycle 2c gives EM 0.503 at 1.5 s / 2.0 s and $0.014 per 1,000 questions with one LLM call; the decomposed agent costs 4× the latency for no EM gain, the team 6×.
- **In practice the checked agent is "RAG plus rules":** one call for 87% of questions, the same median latency as plain RAG, so it is a safe default; the iterative and multi-agent designs are justified only when hop 2 is often missed by a single search and the accuracy gain is worth 4–6× the latency.
