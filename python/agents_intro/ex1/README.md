# Ex1 - Llama 3 Agent (No Library)

This exercise builds a minimal agent without an agent framework:
- LLM call through Ollama (`llama3`).
- System prompt that decides: answer directly or call tool.
- Tools: calculator, current_time, unit_convert.
- Structured JSON contract between model and orchestrator.
- Easy extension point for new tools.

## Prerequisites

- Python 3.14 (or 3.10+ should also work).
- Ollama running locally.
- Llama 3 model available locally.

Use [Ollama website](https://ollama.com/download) to download Ollama CLI.

Install model once (if needed).
```bash
ollama pull llama3
```

## Setup

From the `agents_intro/ex1` directory:

```bash
cd ex1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Interactive chat:

```bash
python agent.py
```

One-shot prompt:

```bash
python agent.py --prompt "What is (15 - 3) * 2?"
```

Optional flags:
- `--model llama3`
- `--base-url http://localhost:11434`
- `--timeout 60`
- `--max-turns 6`

## How tool usage works

The model must output exactly one JSON object:
- Final answer:
  - `{"type":"final_answer","content":"..."}`
- Tool call:
  - `{"type":"tool_call","tool":"calculator","arguments":{"expression":"(12+3)*4"}}`
  - `{"type":"tool_call","tool":"current_time","arguments":{"timezone":"Asia/Jerusalem"}}`
  - `{"type":"tool_call","tool":"unit_convert","arguments":{"value":10,"from_unit":"km","to_unit":"mi"}}`

If output is not valid JSON, the agent sends one repair prompt and retries parsing.

## Validation prompts

Try these prompts:

1. Direct answer (no tool expected):
   - `Explain what a hash table is in one short paragraph.`
2. Calculator tool expected:
   - `What is (14 + 6) / 5?`
3. Mixed reasoning + tool:
   - `Compute 17*19 and then explain in one sentence how you got it.`
4. Current time tool expected:
   - `What time is it now in Asia/Jerusalem?`
5. Unit conversion tool expected:
   - `Convert 10 kilometers to miles.`
6. Unsafe expression handling:
   - `Use calculator for: __import__('os').system('ls')`
7. Unknown tool behavior probe:
   - `Use tool weather_tool for Tel Aviv.`

## Add new tools

In `ex1_agent.py`, extend `self.tools`:

```python
self.tools["my_tool"] = self._tool_my_tool
```

Then implement:

```python
def _tool_my_tool(self, **kwargs):
    ...
```

Update the system prompt with the new tool and when to use it.
