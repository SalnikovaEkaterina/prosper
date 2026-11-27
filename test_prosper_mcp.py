
import asyncio
from unittest.mock import patch
from fastmcp import Client
from src.agent.mcp_server import mcp


async def main():

    with patch.dict("os.environ", {
        "PROSPER_API_URL": "https://example.invalid",
        "PROSPER_API_TOKEN": "mock-token"
    }):

        with patch(
            "src.agent.prosper_http.ProsperClient._request"
        ) as mock:

            mock.return_value = {
                "job_id": "test-job"
            }

            async with Client(mcp) as client:

                result = await client.call_tool(
                    "prosper_read_parameter",
                    {
                        "tag": "TEST.TAG",
                        "session_id": "test-session"
                    }
                )

                print(result.data)

                mock.assert_called_once_with(
                    "POST",
                    "/v1/jobs",
                    {
                        "op": "get",
                        "tag": "TEST.TAG"
                    }
                )

                mock.reset_mock()
                mock.return_value = {"value": 100}

                result = await client.call_tool(
                    "prosper_get_job",
                    {
                        "job_id": "test-job",
                        "session_id": "test-session"
                    }
                )

                print(result.data)

                mock.assert_called_once_with(
                    "GET",
                    "/v1/jobs/test-job"
                )

    print("MCP + HTTP adapter: OK")


if __name__ == "__main__":
    asyncio.run(main())
