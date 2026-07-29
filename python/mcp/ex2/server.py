from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources import FileResource
from mcp.types import ToolAnnotations
from pydantic import AnyUrl

FILES_DIR = Path(__file__).with_name("files").resolve()

mcp = FastMCP("files")


def _safe_path(name: str) -> Path:
    if not name or Path(name).name != name:
        raise ValueError(f"invalid file name: {name!r}")
    path = (FILES_DIR / name).resolve()
    path.relative_to(FILES_DIR)
    return path


for path in sorted(FILES_DIR.iterdir()):
    if path.is_file():
        mcp.add_resource(
            FileResource(
                uri=AnyUrl(f"files://{path.name}"),
                name=path.name,
                path=path,
                mime_type="text/plain",
            )
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
    )
)
def delete_file(name: str) -> str:
    """Delete a file from the exposed files directory."""
    path = _safe_path(name)
    if not path.is_file():
        raise FileNotFoundError(name)
    path.unlink()
    return f"deleted {name}"


if __name__ == "__main__":
    mcp.run()
