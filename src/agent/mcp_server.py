import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from src.agent.tools import register_tools

# Загружаем переменные окружения (.env)
load_dotenv()

# Создаем экземпляр MCP сервера
mcp = FastMCP("PROSPER-Agent")

# Регистрируем наши инструменты
register_tools(mcp)

if __name__ == "__main__":
    # Запускаем MCP сервер по stdio (стандартный протокол для LLM-клиентов)
    mcp.run()
