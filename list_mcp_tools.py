
import asyncio
from fastmcp import Client
from src.agent.mcp_server import mcp

async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()

        for tool in tools:
            print(tool.name)
asyncio.run(main())
