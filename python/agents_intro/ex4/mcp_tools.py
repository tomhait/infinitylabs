"""MCP client helpers for the session-based calculator in ex3_mcp."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DEFAULT_MCP_URL = "http://127.0.0.1:8765/mcp"

MCP_CALCULATOR_TOOLS = frozenset({"let", "calculate", "last_result", "state"})


async def call_tool(session: ClientSession, name: str, arguments: dict[str, Any] | None = None) -> Any:
    result = await session.call_tool(name, arguments or {})
    if result.isError:
        texts = [content.text for content in result.content if hasattr(content, "text")]
        message = texts[0] if texts else str(result)
        raise RuntimeError(message)

    if result.structuredContent is not None:
        if "result" in result.structuredContent:
            return result.structuredContent["result"]
        return result.structuredContent

    texts = [content.text for content in result.content if hasattr(content, "text")]
    if len(texts) == 1:
        return texts[0]
    return texts


@asynccontextmanager
async def mcp_session(url: str = DEFAULT_MCP_URL) -> AsyncIterator[ClientSession]:
    """Open one MCP client session (isolated calculator state)."""
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            try:
                await session.initialize()
            except Exception as error:
                raise RuntimeError(
                    f"Failed to connect to MCP calculator at {url}. "
                    "Start the server first: cd ex3_mcp && python server.py"
                ) from error
            yield session
