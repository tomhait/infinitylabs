# Exercise 2: Parallel Branches and Reducers

Fan out two branches in the same super-step; both write to the same state field.

## What this demonstrates

1. **Without a reducer** — concurrent writes to one key raise `InvalidUpdateError`.
2. **With a reducer** — `Annotated[list, operator.add]` merges both branch updates every run.

## Run

```bash
python3 ex2_graph.py
```

## Files

- `graph.py` — parallel left/right nodes, broken + fixed state schemas

## Takeaway

If more than one node in a super-step writes the same key, that key needs a reducer.
