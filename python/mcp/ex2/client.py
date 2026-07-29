import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).with_name("server.py")


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            resources = await session.list_resources()
            print("resources:")
            for resource in resources.resources:
                print(f"  {resource.uri} ({resource.name})")

            print("\ncontents:")
            for resource in resources.resources:
                result = await session.read_resource(resource.uri)
                for content in result.contents:
                    text = getattr(content, "text", None)
                    print(f"--- {resource.name} ---")
                    print(text if text is not None else content)

            if not resources.resources:
                return

            names = [resource.name for resource in resources.resources]
            print("\nfiles:")
            for i, name in enumerate(names, start=1):
                print(f"  {i}. {name}")

            choice = input("\nFile to delete (number or name, empty to cancel): ").strip()
            if not choice:
                print("cancelled")
                return

            if choice.isdigit():
                index = int(choice)
                if index < 1 or index > len(names):
                    print("invalid selection")
                    return
                target = names[index - 1]
            elif choice in names:
                target = choice
            else:
                print("unknown file")
                return

            tools = await session.list_tools()
            delete_tool = next((t for t in tools.tools if t.name == "delete_file"), None)
            if delete_tool and delete_tool.annotations:
                print(f"\ndelete_file annotations: {delete_tool.annotations}")

            answer = input(f"Delete {target!r}? [y/N] ").strip().lower()
            if answer != "y":
                print("cancelled")
                return

            result = await session.call_tool("delete_file", {"name": target})
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
