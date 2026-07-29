# Exercise 1: Get Time

Minimal MCP server with one tool, `get_time`, and a stdio client that calls it.

## Files

- `server.py` — FastMCP server exposing `get_time`
- `client.py` — starts the server over stdio and calls the tool

## Setup

```bash
pip install mcp
```

## Run

From the `python/mcp` directory:

```bash
python ex1/client.py
```

The client spawns `server.py` with the same Python interpreter and prints the current UTC time.
