# Exercise 4: LLM Validator Loop + Human-in-the-Loop

LLM proposes a 3-word coffee slogan; a validator loops on failure. A fake `send` node is the irreversible side-effect. Two interrupt placements show why veto timing matters.

## What this demonstrates

1. **LLM + validator loop** — `propose` (Ollama `llama3`) → `validate` (exactly 3 words) → loop or continue.
2. **Wrong interrupt (after `send`)** — human rejects, but `sent` is already `True`. Too late.
3. **Right interrupt (before `send`)** — human rejects; `send` never runs; `sent` stays `False`.

## Prerequisites

- Ollama running locally
- `llama3` pulled (`ollama pull llama3`)
- `langchain-ollama` and `langgraph` installed

## Run

```bash
python3 ex4_graph.py
```

## Takeaway

A human interrupt only prevents a side-effect if it sits **before** that node. After `send`, reject cannot undo what already happened.
