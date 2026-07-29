# LangChain Agent (Local Ollama Only)

This exercise reproduces Ex1 behavior using LangChain:
- local Ollama model (`llama3` by default)
- LangChain-managed LLM calls + message objects
- manual tool orchestration loop (same behavior as Ex1)
- tools: `calculator`, `current_time`, `unit_convert`
- interactive mode and one-shot CLI mode

## Prerequisites

- Python 3.14 (or 3.10+)
- Ollama installed and running locally
- Llama model pulled locally

Use [Ollama website](https://ollama.com/download) to download Ollama CLI.

Install model if needed:

```bash
ollama pull llama3
```

## Setup

From `agents_intro/ex2`:

```bash
cd ex2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Interactive:

```bash
python langchain_agent.py
```

One-shot:

```bash
python langchain_agent.py --prompt "Convert 10 km to miles"
```

Optional flags:
- `--model llama3`
- `--base-url http://localhost:11434`
- `--timeout 60`
- `--max-turns 6`

## Validation prompts

1. Direct answer (no tool expected):
   - `Explain in one paragraph what a hash table is.`
2. Calculator tool:
   - `What is (14 + 6) / 5?`
3. Time tool:
   - `What time is it now in Asia/Jerusalem?`
4. Unit conversion tool:
   - `Convert 72 Fahrenheit to Celsius.`
5. Mixed:
   - `Compute 17*19 and then explain briefly how you got it.`

## Notes

- This Ex2 implementation uses local Ollama only (no cloud providers).
- If you see connection errors, verify Ollama is running and reachable at `localhost:11434`.
