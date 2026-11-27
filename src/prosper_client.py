import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

class ProsperClient:
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.token = token
        self.session_id = None

    def _api(self, method, path, *, body=None, session=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        if session:
            headers["X-Session-ID"] = session
        data = None if body is None else json.dumps(body).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        
        req = Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=20) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            try:
                return error.code, json.loads(raw)
            except ValueError:
                return error.code, {"error": raw[:200]}

    def health(self):
        return self._api("GET", "/health")

    def open_session(self):
        status, opened = self._api("POST", "/v1/session")
        if status == 200:
            self.session_id = opened["session_id"]
            return True
        return False

    def close_session(self):
        if self.session_id:
            self._api("DELETE", "/v1/session", session=self.session_id)
            self.session_id = None

    def execute_job(self, operation):
        if not self.session_id:
            return "Ошибка: Сессия не открыта"
            
        status, queued = self._api("POST", "/v1/jobs", session=self.session_id, body=operation)
        if status != 202:
            return f"Ошибка запуска: HTTP {status}, {queued}"
        
        job_id = queued['job_id']
        for _ in range(60):
            st, cur = self._api("GET", f"/v1/jobs/{job_id}", session=self.session_id)
            if st != 200:
                return f"Ошибка чтения статуса: {st}, {cur}"
            if cur['status'] == 'done':
                return cur['result']
            if cur['status'] == 'failed':
                return f"Расчет не выполнен (job_id: {job_id})"
            time.sleep(1)
        return "Таймаут ожидания job"
