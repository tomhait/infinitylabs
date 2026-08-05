# Multi-Agent Debate System

Crudest end-to-end debate pipeline: **retrieve real papers → research findings → Pro → Con → neutral synthesis → deterministic scores**.

Default question:

> Are current frontier LLMs aligned enough for safe general use in public-facing products?

This measures **pipeline health and debate structure**, not objective truth or a final “winner.”

## Pipeline

```
Question + fixed stances
        ↓
[Retrieval]  Semantic Scholar (OpenAlex fallback) → academic sources
        ↓
[Research]   LLM turns abstracts into grounded findings {claim, source_index}
        ↓
[Team Pro] → [Team Con]   up to --rounds (1|2); early-stop if uniqueness collapses
        ↓
[Summarizer] neutral synthesis (no declared winner)
        ↓
[Judge?]     optional rubric verdict via Gemini (--judge)
        ↓
[Scorer]     deterministic pipeline + quality metrics
```

| File | Role |
|------|------|
| `main.py` | CLI entrypoint |
| `state.py` | Shared debate state and fixed stances |
| `llm.py` | Groq / Gemini client + **model tiering** |
| `retrieval.py` | Academic paper retrieval + cache |
| `agents.py` | Research, Pro, Con, summarizer nodes |
| `judge.py` | Optional LLM judge (default: Gemini) |
| `scorer.py` | Deterministic metrics |

## Setup

Create a `.env` file (already gitignored):

```env
groq_api_key=YOUR_GROQ_KEY
gemini_api_key=YOUR_GEMINI_KEY

# Optional model overrides
# GROQ_RESEARCH_MODEL=llama-3.1-8b-instant
# GROQ_DEBATE_MODEL=llama-3.3-70b-versatile
# GROQ_SUMMARY_MODEL=llama-3.1-8b-instant
# JUDGE_PROVIDER=gemini
# JUDGE_MODEL=gemini-flash-latest
```

## Run

```bash
# Default: Groq pipeline with model tiering, 1 round, no judge
python3 main.py

# Up to 2 rounds; stop early if TF-IDF uniqueness < 0.20
python3 main.py --rounds 2

# Rubric verdict via Gemini judge
python3 main.py --judge

# Override tiers
python3 main.py \
  --research-model llama-3.1-8b-instant \
  --debate-model llama-3.3-70b-versatile \
  --summary-model llama-3.1-8b-instant \
  --judge --judge-provider gemini --judge-model gemini-flash-latest

# Custom output path
python3 main.py --out outputs/my_run.txt
```

### Termination policies
1. **Fixed rounds** — `--rounds 1` or `2` (hard cap).
2. **Uniqueness collapse** — after each completed exchange, if `pro_con_uniqueness < --uniqueness-threshold` (default `0.20`), skip further rounds.

### Summary / verdict policy
- Default: **neutral synthesis** only.
- Optional: `--judge` adds a structured rubric verdict (`pro` / `con` / `tie` if margin `< 2`). Judge defaults to **Gemini** (`gemini-flash-latest`), with fallback to the debate provider if Gemini fails.

Writes:

- `outputs/debate_m0.txt` — full transcript
- `outputs/debate_m0.scores.json` — metrics only
- `outputs/retrieval_cache/` — cached paper lists (avoids repeat API hits)

## Metrics

Scores are **deterministic**: same transcript → same numbers. The LLM steps are not.

### Pipeline (pass/fail wiring)

Checks that the question, sources, findings, both arguments, Con↔Pro engagement, and synthesis all exist at minimum length. `pass: true` means the system ran end-to-end — not that a side is correct.

### Quality (debate-oriented)

| Metric | What it measures |
|--------|------------------|
| `peer_reviewed_source_ratio` | Fraction of retrieved sources classified as peer-reviewed (heuristic: journal/conference vs preprint venues) |
| `findings_from_peer_reviewed_ratio` | Fraction of findings citing those sources |
| `doi_source_ratio` | Sources with a DOI |
| `pro_con_uniqueness` | `1 − TF‑IDF cosine` between Pro and Con (lexical distinctness) |
| `con_engages_pro` | Con rebuts Pro (phrase overlap and/or rebuttal markers) |
| `*_overclaim_per_100_words` | Absolute wording (“always”, “never”, “proven”, …) |
| `*_stance_consistency` | Lexical lean toward the assigned stance |
| `*_grounding_rate` | How much each side uses the shared findings / `[n]` cites |

### Why metrics must be deterministic

LLM outputs vary across runs. Fixed code metrics let you compare versions of the system (better research, more rounds, etc.) without mistaking model randomness for product improvement.

## Design notes

- **Stances are assigned before the run** — agents do not choose sides.
- **Research is retrieval-backed** so findings cite real papers instead of invented citations.
- **Peer-reviewed flags are heuristics**, not a guarantee of formal peer review.
- Semantic Scholar free tier often returns HTTP 429; the pipeline falls back to OpenAlex and caches results.
- Adding complexity (multi-round debate, team subgraphs, a judge node) should wait until a baseline score is stable and each addition improves a metric you care about.

## Example score shape

```json
{
  "pipeline": { "pass": true, "total": 7, "max_total": 7 },
  "quality": {
    "peer_reviewed_source_ratio": 0.5,
    "pro_con_uniqueness": 0.34,
    "con_engages_pro": true,
    "mean_grounding_rate": 1.0
  }
}
```

## Cost savings (key levers)

Default cheap profile: **Groq debate pipeline + optional Gemini judge**, with roles split by model size.

| Lever | What we do | Why it saves |
|--------|------------|--------------|
| **Model tiering** | Research + summarizer → `llama-3.1-8b-instant`; Pro/Con → `llama-3.3-70b-versatile` | Most calls are extraction/formatting; only arguments use the expensive model |
| **Judge off by default** | `--judge` is optional; when on, uses **Gemini Flash**, not a second 70B call on every run | Avoids an extra full LLM pass unless you need a verdict |
| **One round by default** | `--rounds 1`; `--rounds 2` only when needed | Each round = 2 debate calls (Pro + Con) |
| **Early stop** | Skip round 2 if TF‑IDF uniqueness collapses | Stops paying for repetitive exchanges |
| **Token caps** | Research `800`, Pro/Con `450`, summary `350`, **judge `2048`** (needs room for full JSON); synthesis asked for ≤200 words | Caps cut cost on long generations; judge is higher so the verdict JSON is not truncated |
| **Retrieval cache** | `outputs/retrieval_cache/` | Avoids repeat paper fetches across runs |
| **Single-node teams** | Pro/Con are one agent each | No specialist swarm multiplying calls |
| **Truncated abstracts** | Research sees title + clipped abstract, not full PDFs | Smaller research prompts |

**Confidence to cut further:** compare `pipeline.pass`, `mean_grounding_rate`, `con_engages_pro`, and uniqueness before/after changing a tier. If those stay stable, keep the cheaper setting.

Example overrides:

```bash
# Absolute cheapest smoke test (weaker arguments)
python3 main.py \
  --debate-model llama-3.1-8b-instant \
  --research-model llama-3.1-8b-instant \
  --summary-model llama-3.1-8b-instant

# Default recommended production-of-MVP profile
python3 main.py --rounds 1
# + verdict only when needed:
python3 main.py --judge
```
