
from unittest.mock import patch

from src.agent.prosper_http import ProsperClient

with patch.dict("os.environ", {
    "PROSPER_API_URL": "https://example.invalid",
    "PROSPER_API_TOKEN": "mock-token"
}):
    client = ProsperClient()

with patch.object(client, "_request") as mock:

    mock.return_value = {
        "session_id": "test-session"
    }

    client.open_session()

    assert client.session_id == "test-session"
    print("OK: открытие сессии")

    mock.return_value = {
        "job_id": "test-job"
    }

    result = client.read_parameter("TEST.TAG")

    mock.assert_called_with(
        "POST",
        "/v1/jobs",
        {"op": "get", "tag": "TEST.TAG"}
    )

    assert result["job_id"] == "test-job"
    print("OK: формирование задания")

    mock.return_value = {
        "value": 100
    }

    result = client.get_job("test-job")

    assert result["value"] == 100
    print("OK: получение результата")

    mock.return_value = {}

    client.close_session()

    assert client.session_id is None
    print("OK: закрытие сессии")

print("Все локальные проверки пройдены")
