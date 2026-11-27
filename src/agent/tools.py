from mcp.server.fastmcp import FastMCP
import os
from src.prosper_client import ProsperClient

# Инициализируем клиент PROSPER
prosper = ProsperClient(
    base_url=os.getenv("PROSPER_API_URL", ""),
    token=os.getenv("PROSPER_API_TOKEN", "")
)

def register_tools(mcp: FastMCP):
    """Регистрирует все инструменты в MCP-сервере."""
    
    @mcp.tool()
    def get_prosper_parameter(tag: str) -> str:
        """Читает значение параметра из модели PROSPER по его тегу (например, 'PROSPER.PVT.Input.Solgor')."""
        if not prosper.session_id:
            prosper.open_session()
        result = prosper.execute_job({"op": "get", "tag": tag})
        return str(result)

    @mcp.tool()
    def set_prosper_parameter(tag: str, value: str) -> str:
        """Устанавливает значение параметра в модели PROSPER. Изменяет общую модель."""
        if not prosper.session_id:
            prosper.open_session()
        result = prosper.execute_job({"op": "set", "tag": tag, "value": value})
        return str(result)

    @mcp.tool()
    def run_prosper_calculation(command_id: str) -> str:
        """Запускает расчет в PROSPER. Доступные команды: pvt_calculate, inflow_calculate, system_calculate."""
        if not prosper.session_id:
            prosper.open_session()
        result = prosper.execute_job({"op": "run", "command_id": command_id})
        return str(result)
        result = prosper.execute_job({"op": "run", "command_id": command_id})
        return str(result)
