from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("get-time")


@mcp.tool()
def get_time() -> str:
    """Return the current UTC time as ISO-8601."""
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    mcp.run()
