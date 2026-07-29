# Two-Agent Python Code Review Evaluation

Generate buggy Python (Agent A) → review without knowing `x` (Agent B) → deterministic Precision/Recall/F1 + nice reports.

## Design

- **`x = 12` planted bugs** per generated file (fixed budget for stable metrics)
- Bug mix:
  - logic ×4
  - edge_case ×2
  - security ×2
  - performance ×2
  - api_design ×1
  - maintainability ×1
- Generator and reviewer use **different Ollama models** by default
- Evaluator is **deterministic** (line overlap + category + text similarity)
- Reporting:
  - per-trial Markdown + JSON artifacts
  - aggregate `summary.md` / `summary.json`
  - CLI headline banner

## Prerequisites

- Python 3.10+ (3.14 ok with LangChain warning suppressed)
- Local Ollama running
- Two models available (example):

Use [Ollama website](https://ollama.com/download) to download Ollama CLI.

```bash
ollama pull llama3
ollama pull llama3.1
```

If you only have one model, pass the same name to both flags (results are still valid, but less diverse).

## Setup

```bash
cd ex3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Offline demo (no LLM calls; validates eval + reporting):

```bash
python run_experiment.py --demo
```

Full experiment (default 5 trials, `x=12`):

```bash
python run_experiment.py \
  --trials 5 \
  --generator-model llama3 \
  --reviewer-model llama3.1
```

Useful flags:
- `--topic "inventory service helpers"`
- `--output-dir runs/my_run`
- `--match-threshold 0.55`
- `--timeout 180`
- `--base-url http://localhost:11434`

## Outputs

```text
runs/<timestamp>/
  summary.md
  summary.json
  trial_01/
    generated_code.py
    ground_truth.json
    review_findings.json
    matches.json
    trial_report.md
    trial_metrics.json
  trial_02/
    ...
```

Open `summary.md` for the human-facing report.

## Review a single Python file

Review any local `.py` file by path:

```bash
python review_file.py --file ../ex1/agent.py --model llama3.1
```

Optional focus:

```bash
python review_file.py --file ../ex1/agent.py --focus security
```

Outputs:

```text
reviews/<timestamp>/
  review_report.md
  review_findings.json
```

## How matching works

Choose with `--match-mode`:

| Mode | Decision |
|------|----------|
| `deterministic` (default) | category + line overlap + token Jaccard ≥ `--match-threshold` |
| `embeddings` | cosine(embed(truth), embed(finding)) ≥ `--embed-threshold` |
| `llm_judge` | judge LLM returns `match=true` with confidence ≥ `--judge-threshold` |
| `all` | **yes if any** of the three methods says yes (OR), else no |

Examples:

```bash
python run_experiment.py --demo --match-mode deterministic
python run_experiment.py --demo --match-mode embeddings
python run_experiment.py --demo --match-mode all
python run_experiment.py --trials 3 --match-mode llm_judge --judge-model llama3.1
```

Notes:
- Embeddings prefer Ollama (`--embed-model`, default `nomic-embed-text`). If unavailable, falls back to local TF-IDF cosine.
- `all` short-circuits: if deterministic already matches a pair, embeddings/LLM are not required for that pair.
- Each matched pair in `matches.json` includes `yes_modes` / `votes` for auditability.

A reviewer finding is a **true positive** if the selected matcher accepts the pair, then greedy 1-to-1 assignment is applied.

Then:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = harmonic mean

## Notes

- Python files only (no git/PR integration in this version)
- Generator emits **two blocks** (` ```python ` then ` ```json `) so source code is not embedded inside JSON (avoids parse errors from quotes/newlines)
- Generator must emit valid Python + exact category budget or the trial retries/fails
- Reviewer never receives `x` or ground truth
