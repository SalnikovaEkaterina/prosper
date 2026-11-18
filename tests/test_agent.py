
import asyncio

from fastmcp import Client

from src.agent.mcp_server import mcp


async def call_tubing(id_mm):
    async with Client(mcp) as client:
        response = await client.call_tool(
            "check_tubing",
            {
                "well_id": "W-31",
                "od_mm": 73,
                "wall_mm": 5.5,
                "id_mm": id_mm,
            },
        )
        return response.data


def test_valid_tubing():
    result = asyncio.run(call_tubing(62))

    assert result["status"] == "PRECHECK_OK"
    assert result["result"]["expected_id_mm"] == 62
    assert result["trace_id"]


def test_invalid_tubing():
    result = asyncio.run(call_tubing(80))

    assert result["status"] == "INVALID_INPUT"
    assert "62.00" in result["reason"]
    assert result["trace_id"]
