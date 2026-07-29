import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8765/mcp"


async def call(session: ClientSession, name: str, arguments: dict | None = None):
    result = await session.call_tool(name, arguments or {})
    if result.isError:
        texts = [c.text for c in result.content if hasattr(c, "text")]
        return texts[0] if texts else result
    if result.structuredContent is not None:
        if "result" in result.structuredContent:
            return result.structuredContent["result"]
        return result.structuredContent
    texts = [c.text for c in result.content if hasattr(c, "text")]
    return texts[0] if len(texts) == 1 else texts


async def handle(session: ClientSession, line: str) -> bool:
    parts = line.split(maxsplit=1)
    if not parts:
        return True
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if cmd in {"q", "quit", "exit"}:
        return False
    if cmd in {"h", "help"}:
        print("commands: let <name> <value> | calc <expr> | last | state | help | quit")
        return True
    if cmd == "let":
        tokens = rest.split()
        if len(tokens) != 2:
            print("usage: let <name> <value>")
            return True
        name, value = tokens
        print(await call(session, "let", {"name": name, "value": float(value)}))
        return True
    if cmd in {"calc", "calculate"}:
        if not rest:
            print("usage: calc <expression>")
            return True
        print(await call(session, "calculate", {"expression": rest}))
        return True
    if cmd in {"last", "last_result"}:
        print(await call(session, "last_result"))
        return True
    if cmd == "state":
        print(await call(session, "state"))
        return True
    print("unknown command; type help")
    return True


async def main() -> None:
    async with streamable_http_client(URL) as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("connected. type help for commands.")
            while True:
                try:
                    line = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not await handle(session, line):
                    break


if __name__ == "__main__":
    asyncio.run(main())
