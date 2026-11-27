
import os
import requests

from dotenv import load_dotenv
from urllib.parse import quote


class ProsperAPIError(Exception):
    """Ошибка взаимодействия с API PROSPER."""
    pass


class ProsperClient:

    def __init__(self):
        load_dotenv()

        self.base_url = os.getenv(
            "PROSPER_API_URL", ""
        ).rstrip("/")

        self.token = os.getenv(
            "PROSPER_API_TOKEN", ""
        )

        self.session_id = None

        if not self.base_url or not self.token:
            raise ProsperAPIError(
                "Не заданы настройки API PROSPER"
            )

    def _request(self, method, path, payload=None):
        """Общая функция отправки HTTP-запросов."""

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        if self.session_id:
            headers["X-Session-Id"] = self.session_id

        try:
            response = requests.request(
                method=method,
                url=self.base_url + path,
                headers=headers,
                json=payload,
                timeout=30
            )

        except requests.Timeout:
            raise ProsperAPIError(
                "Превышено время ожидания API"
            ) from None

        except requests.RequestException:
            raise ProsperAPIError(
                "Ошибка соединения с API"
            ) from None

        if not response.ok:
            raise ProsperAPIError(
                f"Ошибка API: HTTP {response.status_code}"
            )

        if not response.content:
            return {}

        try:
            return response.json()

        except ValueError:
            raise ProsperAPIError(
                "API вернул некорректный JSON"
            ) from None

    def open_session(self):
        """Открытие рабочей сессии."""

        if self.session_id:
            raise ProsperAPIError("Сессия уже открыта")

        data = self._request("POST", "/v1/session")
        self.session_id = data["session_id"]

        return data

    def close_session(self):
        """Закрытие рабочей сессии."""

        if self.session_id:
            self._request("DELETE", "/v1/session")
            self.session_id = None

    def _require_session(self):
        if not self.session_id:
            raise ProsperAPIError("Сессия не открыта")

    def get_model(self):
        """Получение информации о модели."""

        self._require_session()
        return self._request("GET", "/v1/model")

    def read_parameter(self, tag):
        """Отправка задания на чтение параметра."""

        self._require_session()

        if not tag or len(tag) > 180:
            raise ProsperAPIError("Некорректный tag")

        return self._request(
            "POST",
            "/v1/jobs",
            {
                "op": "get",
                "tag": tag
            }
        )

    def get_job(self, job_id):
        """Получение состояния и результата задания."""

        self._require_session()

        return self._request(
            "GET",
            "/v1/jobs/" + quote(str(job_id), safe="")
        )


    def wait_job(self, job_id, timeout=60, interval=3):
        """Ожидание завершения задания."""
        import time

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:

            data = self.get_job(job_id)

            status = str(
                data.get("status", "")
            ).lower()

            if status in {
                "success", "completed",
                "done", "succeeded"
            }:
                return data

            if status in {
                "failed", "error", "cancelled",
                "timeout"
            }:
                raise ProsperAPIError(
                    f"Задание завершилось: {status}"
                )

            if status not in {
                "queued", "pending", "running"
            }:
                raise ProsperAPIError(
                    "Неизвестный статус задания"
                )

            remaining = deadline - time.monotonic()

            if remaining > 0:
                time.sleep(min(interval, remaining))

        raise ProsperAPIError(
            "Превышено время ожидания задания"
        )
