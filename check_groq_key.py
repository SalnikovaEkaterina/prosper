
import os
from dotenv import load_dotenv

load_dotenv(override=True)

key = os.getenv("GROQ_API_KEY", "")

print("Ключ найден:", bool(key))
print("Формат Groq:", key.startswith("gsk_"))
print("Длина ключа:", len(key))
