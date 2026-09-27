# Exercise 5: Capstone — One ReAct Agent Node

Replace the single LLM `propose` node with a ReAct-style tool-using agent (from Agents Intro). Keep one agent node only.

## What this demonstrates

1. **Agent node** — `propose` runs the copied Agents Intro agent (`calculator` / `current_time` / `unit_convert`) until a final answer, then writes `draft`.
2. **Outer graph unchanged in spirit** — validate (3 words) → human interrupt **before** `send` → approve/reject.
3. **State schema change** — `agent_messages: Annotated[list[str], operator.add]` holds the agent's internal scratch (user / model / tool turns).

### What had to change about the state schema?

Yes — the agent needs its own scratch/messages field.

The outer graph loop (`propose` ↔ `validate`) and the agent's inner ReAct loop are different. Outer fields like `draft` only store the final slogan. Without `agent_messages`, tool calls and intermediate model turns would have nowhere to live in graph state (or would overwrite each other). A dedicated list + reducer lets each agent run append its scratch without colliding with parallel or later updates.

## Prerequisites

- Ollama running locally with `llama3`
- `langchain-ollama`, `langchain-core`, `langgraph` installed

## Run

```bash
python3 ex5_graph.py
```

## Files

- `langchain_agent.py` — copied from `agents_intro/ex2`, plus `run_with_messages` for scratch tracing
- `ex5_graph.py` — LangGraph with one agent node

## Takeaway

One agent node is enough here; give it its own messages/scratch in state. A team of agents is the next module.
