
import asyncio
import json

from fastmcp import Client

from src.agent.mcp_server import mcp


async def main():
    async with Client(mcp) as client:

        print("\n=== УСПЕШНЫЙ ЗАПРОС ===")

        success = await client.call_tool(
            "check_tubing",
            {
                "well_id": "W-31",
                "od_mm": 73,
                "wall_mm": 5.5,
                "id_mm": 62,
            },
        )

        print(json.dumps(
            success.data,
            ensure_ascii=False,
            indent=2,
        ))

        print("\n=== НЕКОРРЕКТНЫЙ ВХОД ===")

        failure = await client.call_tool(
            "check_tubing",
            {
                "well_id": "W-31",
                "od_mm": 73,
                "wall_mm": 5.5,
                "id_mm": 80,
            },
        )

        print(json.dumps(
            failure.data,
            ensure_ascii=False,
            indent=2,
        ))


if __name__ == "__main__":
    asyncio.run(main())

