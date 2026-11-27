import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from src.agent.tools import register_tools, prosper

# Загружаем переменные окружения (.env)
load_dotenv()

# Создаем экземпляр MCP сервера
mcp = FastMCP("PROSPER-Agent")

# Регистрируем наши инструменты
register_tools(mcp)

# Событие при запуске сервера
@mcp.on_startup()
async def startup():
    # Проверяем здоровье и открываем сессию PROSPER
    status, _ = prosper.health()
    if status == 200:
        prosper.open_session()
        print("✅ PROSPER: Сессия открыта.")
    else:
        print("❌ PROSPER: Сервер недоступен.")

# Событие при остановке сервера
@mcp.on_shutdown()
async def shutdown():
    # Обязательно закрываем сессию, чтобы не блокировать других
    prosper.close_session()
    print("🔌 PROSPER: Сессия закрыта.")

if __name__ == "__main__":
    # Запускаем MCP сервер по stdio (стандартный протокол для LLM-клиентов)
    mcp.run()
