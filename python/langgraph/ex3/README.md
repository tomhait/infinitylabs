# Exercise 3: Checkpointers

Add an in-memory checkpointer and a `thread_id`. Simulate a crash, resume from the last checkpoint, then mutate checkpoint state outside a node.

## What this demonstrates

1. **Crash mid-run** — node `b` raises; checkpoint keeps state after `a` with `next=('b',)`.
2. **Resume** — `update_state` clears the failure flag, then `invoke(None, config)` continues from that checkpoint.
3. **Mutate outside a node — what happens on the next invoke?**
   `update_state` writes a new checkpoint with your patched values. The next `invoke` on that `thread_id` uses that mutated state.
   - If the graph was already finished (`next=()`), nodes do **not** re-run; invoke returns the mutated values as-is.
   - If work was still pending (`next` is not empty), invoke **resumes from that point** and later nodes see the mutated values.

## Run

```bash
python3 ex3_graph.py
```

## Takeaway

Checkpoints are per `thread_id`. Failed steps leave you at the last good checkpoint; `update_state` can edit that state before the next invoke.
