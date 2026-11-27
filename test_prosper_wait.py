
from unittest.mock import patch

from src.agent.prosper_http import (
    ProsperClient,
    ProsperAPIError
)

with patch.dict("os.environ", {
    "PROSPER_API_URL": "https://example.invalid",
    "PROSPER_API_TOKEN": "mock-token"
}):
    client = ProsperClient()


# Тест 1. Успешное выполнение

with patch.object(client, "get_job") as mock:

    mock.side_effect = [
        {"status": "queued"},
        {"status": "running"},
        {"status": "completed", "value": 100}
    ]

    result = client.wait_job(
        "test-job", interval=0
    )

    assert result["value"] == 100
    assert mock.call_count == 3

    print("OK: успешное завершение")


# Тест 2. Ошибка выполнения

with patch.object(client, "get_job") as mock:

    mock.return_value = {"status": "failed"}

    try:
        client.wait_job("test-job")
        raise AssertionError("Ожидалась ошибка")

    except ProsperAPIError:
        print("OK: обработка ошибки")


# Тест 3. Таймаут

with patch.object(client, "get_job") as mock:

    mock.return_value = {"status": "running"}

    try:
        client.wait_job(
            "test-job", timeout=1, interval=0.1
        )
        raise AssertionError("Ожидался таймаут")

    except ProsperAPIError:
        print("OK: обработка таймаута")


print("Все тесты пройдены")
