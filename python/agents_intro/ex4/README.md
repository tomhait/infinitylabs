# Ex4 - Join Agents Intro with MCP Session Calculator

Wire the Ex3 tool-using agent to call the session-based calculator over MCP instead of a local Python function.

## Architecture

```text
agent_mcp.py  --HTTP-->  Ollama (llama3)
     |
     +--MCP-->  server.py (let, calculate, last_result, state)
```

Each agent instance opens **one MCP `ClientSession`**. The MCP server isolates calculator state per session (`id(ctx.session)`), so parallel agents do not leak variables or `last_result`.

## Prerequisites

- Ollama running locally with your model pulled
- Python deps for Ex4 and Ex3 MCP server

```bash
pip install -r ex4/requirements.txt
pip install mcp uvicorn
```

## Run

Terminal 1 — start MCP calculator server:

```bash
python server.py
```

Terminal 2 — run Ex4 agent:

```bash
python agent_mcp.py
```

One-shot example:

```bash
python agent_mcp.py --prompt "Set x to 10, calculate x+5, and tell me the result."
```

Useful flags:
- `--model llama3`
- `--mcp-url http://127.0.0.1:8765/mcp`
- `--max-turns 8`

## MCP calculator tools used by the agent

| Tool | Arguments | Purpose |
|------|-----------|---------|
| `let` | `name`, `value` | Store variable in this MCP session |
| `calculate` | `expression` | Evaluate expression (may use `let` vars) |
| `last_result` | `{}` | Return last `calculate` result |
| `state` | `{}` | Return `last_result` + symbol table |

Local (non-MCP) tools kept from Ex1:
- `current_time`
- `unit_convert`

## What changed vs MCP Ex3

| Ex3 (local)                        | Ex4 (MCP) |
|------------------------------------|-----------|
| `self.tools["calculator"](**args)` | `self.mcp.call_tool("calculate", args)` |
| in-process function registry       | remote MCP `tools/call` |
| no transport                       | streamable HTTP MCP client |
| stateless one-shot eval            | session state (`let`, `last_result`, `state`) |

The LLM loop, JSON contract, and repair flow stay the same. Only the calculator backend changed.

## Parallel sessions

If you open multiple agent processes (or multiple `CalculatorMcpClient` instances), each gets its own MCP session and isolated calculator state.

They only share state if they reuse the same MCP client session object.

## Suggested test prompts

1. `Let x be 10 and calculate x * 2 + 3`
2. `Calculate 100 / 4, then subtract 10 from the result`
3. Run two agents in parallel with different `let` values and verify they do not overwrite each other

## Assignment questions

### What has to change in your agent’s tool-invocation code?
In Ex3, `calculator` was executed by calling a local Python function directly:
- `result = local_function(**args)`

In Ex4, the agent routes calculator-related tool calls through MCP instead:
- `result = mcp_client.call_tool(<tool_name>, <arguments>)`

Concretely for this repo (`agent_mcp.py`):
- `_execute_tool_call(...)` checks whether the requested tool is one of the MCP tools (`let`, `calculate`, `last_result`, `state`)
- when it is, it calls `mcp.call_tool(tool_name, args)` instead of invoking a function from a local registry
- the transport/lifecycle is handled via `mcp_session(...)` (open MCP session once per agent run, reuse it for all tool calls)

### If you open multiple agent sessions in parallel, does each one get its own calculator session state? Why or why not?
Yes—each parallel agent process (or each independent `CalculatorMcpClient` / MCP `ClientSession` instance) gets its own isolated calculator state.

Why:
- the Ex3 MCP server stores `SessionState` keyed by `id(ctx.session)`
- Ex4 opens one MCP `ClientSession` per agent run (`async with mcp_session(...) as session:`) and reuses it
- therefore, parallel agents have different MCP `ClientSession` objects, so their `id(ctx.session)` keys differ and state (symbols + `last_result`) does not leak

State would only be shared if you intentionally reused the same MCP `ClientSession` (same `session` object) across multiple agent runs.

## Files

- `mcp_tools.py` — sync-friendly MCP client wrapper
- `agent_mcp.py` — Ex1-style agent with MCP calculator tools
