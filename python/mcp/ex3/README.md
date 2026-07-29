# Exercise 3: Session-based Calculator

MCP calculator with per-session state. One shared streamable-HTTP server can host multiple sessions without leaking variables or last results between them.

## Files

- `server.py` — streamable HTTP server on `127.0.0.1:8765`
- `client.py` — interactive single-session client
- `parallel_client.py` — interactive client with two parallel sessions (A and B)

## Tools

| Tool | Description |
|------|-------------|
| `let(name, value)` | Store a variable in this session |
| `calculate(expression)` | Evaluate arithmetic (may use session variables) |
| `last_result()` | Return this session's last calculation |
| `state()` | Return `last_result` and the symbol table |

## Setup

```bash
pip install mcp uvicorn
```

## Run

Start the server:

```bash
python ex3/server.py
```

In another terminal, either:

```bash
python ex3/client.py
```

or:

```bash
python ex3/parallel_client.py
```

### Single client commands

```text
> let x 10
> calc x * 2 + 1
> last
> state
> quit
```

### Parallel client commands

Prefix with `a` or `b` to choose the session:

```text
> a calc 1+1
> b calc 5*5
> a let x 3
> b state
> quit
```
