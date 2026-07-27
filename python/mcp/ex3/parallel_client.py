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


async def handle(label: str, session: ClientSession, line: str) -> None:
    parts = line.split(maxsplit=1)
    if not parts:
        return
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if cmd in {"h", "help"}:
        print("commands: let <name> <value> | calc <expr> | last | state | help")
        return
    if cmd == "let":
        tokens = rest.split()
        if len(tokens) != 2:
            print("usage: let <name> <value>")
            return
        name, value = tokens
        print(f"{label}:", await call(session, "let", {"name": name, "value": float(value)}))
        return
    if cmd in {"calc", "calculate"}:
        if not rest:
            print("usage: calc <expression>")
            return
        print(f"{label}:", await call(session, "calculate", {"expression": rest}))
        return
    if cmd in {"last", "last_result"}:
        print(f"{label}:", await call(session, "last_result"))
        return
    if cmd == "state":
        print(f"{label}:", await call(session, "state"))
        return
    print("unknown command; type help")


async def main() -> None:
    async with streamable_http_client(URL) as (read_a, write_a, _):
        async with streamable_http_client(URL) as (read_b, write_b, _):
            async with ClientSession(read_a, write_a) as session_a:
                async with ClientSession(read_b, write_b) as session_b:
                    await session_a.initialize()
                    await session_b.initialize()
                    sessions = {"a": session_a, "b": session_b}
                    print("connected to sessions A and B.")
                    print("prefix commands with a or b, e.g. a calc 1+1")
                    print("type help or quit")
                    while True:
                        try:
                            line = input("> ").strip()
                        except (EOFError, KeyboardInterrupt):
                            print()
                            break
                        if not line:
                            continue
                        parts = line.split(maxsplit=1)
                        head = parts[0].lower()
                        if head in {"q", "quit", "exit"}:
                            break
                        if head in {"h", "help"} and len(parts) == 1:
                            print(
                                "usage: <a|b> <command>\n"
                                "commands: let <name> <value> | calc <expr> | last | state | help | quit"
                            )
                            continue
                        if head not in sessions:
                            print("start with a or b, e.g. a calc 1+1")
                            continue
                        command = parts[1] if len(parts) > 1 else ""
                        await handle(head.upper(), sessions[head], command)


if __name__ == "__main__":
    asyncio.run(main())
