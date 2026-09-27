# Exercise 1: Deterministic Graphs

Build a purely deterministic LangGraph with no LLM calls: a node produces a value, a conditional edge loops until a condition is met, then routes to END.

## What this demonstrates

1. **Happy / fixed path** — increment `value` until `value >= target`, then END.
2. **Part (a)** — same wiring but the node never changes `value`, so END is unreachable. Running with the default recursion limit raises `GraphRecursionError`.
3. **Band-aid vs real fix** — raising `recursion_limit` only delays the crash. The real fix is making progress toward a reachable stop condition.

## Run

From this directory (assumes `langgraph` is already installed for your Python):

```bash
python3 ex1_graph.py
```

## Files

- `graph.py` — state, nodes, conditional edges, broken + fixed demos

## Takeaway

`recursion_limit` is a guardrail. A reachable END (node progresses + router can stop) is the design fix.
