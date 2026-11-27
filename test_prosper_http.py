
import asyncio
import json

from fastmcp import Client
from src.agent.mcp_server import mcp


async def main():
    async with Client(mcp) as client:
        response = await client.call_tool(
            "prosper_read_solgor",
            {},
        )

        print("=== REAL PROSPER HTTP RESULT ===")
        print(json.dumps(
            response.data,
            ensure_ascii=False,
            indent=2,
        ))


if __name__ == "__main__":
    asyncio.run(main())
