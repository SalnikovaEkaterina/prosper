from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastmcp import FastMCP
from pydantic import ValidationError

from src.agent.schemas import AgentResult, TubingInput

mcp = FastMCP("PROSPER MCP Adapter")
LOG_FILE = Path("logs/mcp_calls.jsonl")


def write_log(record: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _mock_result(status: str, well_id: str | None, trace_id: str, result: dict | None = None, reason: str = "") -> dict:
    answer = AgentResult(status=status, well_id=well_id, trace_id=trace_id, result=result, reason=reason)
    return answer.model_dump()


@mcp.tool()
def check_tubing(well_id: str, od_mm: float, wall_mm: float, id_mm: float) -> dict:
    """Проверка геометрии НКТ перед переносом в PROSPER. Размеры в мм."""
    trace_id = str(uuid4())
    arguments = {"well_id": well_id, "od_mm": od_mm, "wall_mm": wall_mm, "id_mm": id_mm}
    try:
        data = TubingInput(**arguments)
        expected_id = data.od_mm - 2 * data.wall_mm
        if expected_id <= 0:
            raise ValueError("Толщина стенки несовместима с наружным диаметром")
        if abs(data.id_mm - expected_id) > 0.01:
            raise ValueError(f"Неверный внутренний диаметр: ожидается {expected_id:.2f} мм, получено {data.id_mm:.2f} мм")
        answer = _mock_result("PRECHECK_OK", data.well_id, trace_id, {
            "expected_id_mm": round(expected_id, 2),
            "geometry_valid": True,
            "backend": "MOCK_PROSPER",
            "integration_status": "NOT_CHECKED",
        })
    except (ValidationError, ValueError) as error:
        answer = _mock_result("INVALID_INPUT", well_id, trace_id, reason=str(error))
    write_log({"timestamp": datetime.now(timezone.utc).isoformat(), "trace_id": trace_id, "tool": "check_tubing", "arguments": arguments, "response": answer})
    return answer


@mcp.tool()
def prepare_new_model_plan(well_id: str | None, change: dict | None = None) -> dict:
    """Mock-адаптер: формирует план создания модели New без записи в PROSPER."""
    trace_id = str(uuid4())
    answer = _mock_result("PLAN_READY", well_id, trace_id, {
        "operation": "NEW",
        "backend": "MOCK_PROSPER",
        "integration_status": "NOT_CHECKED",
        "write_executed": False,
        "next_step": "Подключить MCP-инструмент, вызывающий PROSPER/OpenServer после подтверждения инженера.",
        "change": change or {},
    })
    write_log({"timestamp": datetime.now(timezone.utc).isoformat(), "trace_id": trace_id, "tool": "prepare_new_model_plan", "arguments": {"well_id": well_id, "change": change or {}}, "response": answer})
    return answer


@mcp.tool()
def prepare_update_model_plan(well_id: str | None, change: dict | None = None) -> dict:
    """Mock-адаптер: формирует diff-план ремонта без изменения модели."""
    trace_id = str(uuid4())
    answer = _mock_result("PLAN_READY", well_id, trace_id, {
        "operation": "REP",
        "backend": "MOCK_PROSPER",
        "integration_status": "NOT_CHECKED",
        "write_executed": False,
        "confirmation_required": True,
        "next_step": "После подтверждения инженера передать diff реальному PROSPER MCP-адаптеру.",
        "change": change or {},
    })
    write_log({"timestamp": datetime.now(timezone.utc).isoformat(), "trace_id": trace_id, "tool": "prepare_update_model_plan", "arguments": {"well_id": well_id, "change": change or {}}, "response": answer})
    return answer


if __name__ == "__main__":
    mcp.run()


from src.agent.prosper_http import ProsperClient


@mcp.tool()
def prosper_read_parameter(
    tag: str,
    session_id: str
) -> dict:
    """Отправляет задание на чтение параметра PROSPER
    по его точному адресу OpenServer.
    Не изменяет модель.
    """

    client = ProsperClient()
    client.session_id = session_id

    return client.read_parameter(tag)


@mcp.tool()
def prosper_get_job(
    job_id: str,
    session_id: str
) -> dict:
    """Получает состояние и результат задания PROSPER."""

    client = ProsperClient()
    client.session_id = session_id

    return client.get_job(job_id)
