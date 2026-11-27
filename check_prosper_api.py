
import json
import os
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

load_dotenv(override=True)

base_url = os.getenv("PROSPER_API_URL", "").rstrip("/")

if not base_url:
    raise RuntimeError("Не задан PROSPER_API_URL в .env")

try:
    with urlopen(base_url + "/health", timeout=15) as response:
        data = json.load(response)

    print("=== PROSPER API HEALTH ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    if data.get("calculation_verified") is True:
        print("Сервер сообщает о проверенной работе расчётов.")
    else:
        print("Работоспособность расчётов не подтверждена.")

except HTTPError as error:
    print("Ошибка HTTP:", error.code)

except URLError as error:
    print("Сервер недоступен:", error.reason)
