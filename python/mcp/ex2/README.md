# Exercise 2: Files as a Resource

MCP server that exposes a directory of files as resources, plus a `delete_file` tool that requires client-side approval.

## Files

- `server.py` — lists `files/` as MCP resources and provides sandboxed `delete_file`
- `client.py` — lists resources, reads contents, then asks which file to delete
- `files/` — sample files exposed as resources

## Setup

```bash
pip install mcp
```

## Run

From the `python/mcp` directory:

```bash
python ex2/client.py
```

The client will:

1. List resources under `files/`
2. Read and print each file
3. Ask which file to delete (number or name)
4. Ask for explicit `y` confirmation before calling `delete_file`
