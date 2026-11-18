
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastmcp import FastMCP
from pydantic import ValidationError

from src.agent.schemas import TubingInput, AgentResult


mcp = FastMCP("PROSPER Preflight MCP")

LOG_FILE = Path("logs/mcp_calls.jsonl")


def write_log(record: dict):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@mcp.tool()
def check_tubing(
    well_id: str,
    od_mm: float,
    wall_mm: float,
    id_mm: float
) -> dict:
    """
    Проверка геометрии НКТ перед переносом в PROSPER.
    Все размеры задаются в миллиметрах.
    """
    trace_id = str(uuid4())

    arguments = {
        "well_id": well_id,
        "od_mm": od_mm,
        "wall_mm": wall_mm,
        "id_mm": id_mm,
    }

    try:
        data = TubingInput(**arguments)

        expected_id = data.od_mm - 2 * data.wall_mm

        if expected_id <= 0:
            raise ValueError(
                "Толщина стенки несовместима с наружным диаметром"
            )

        if abs(data.id_mm - expected_id) > 0.01:
            raise ValueError(
                f"Неверный внутренний диаметр: "
                f"ожидается {expected_id:.2f} мм, "
                f"получено {data.id_mm:.2f} мм"
            )

        answer = AgentResult(
            status="PRECHECK_OK",
            well_id=data.well_id,
            trace_id=trace_id,
            result={
                "expected_id_mm": round(expected_id, 2),
                "geometry_valid": True,
                "backend": "LOCAL_PREFLIGHT",
            },
        )

    except (ValidationError, ValueError) as error:
        answer = AgentResult(
            status="INVALID_INPUT",
            well_id=well_id,
            trace_id=trace_id,
            reason=str(error),
        )

    result = answer.model_dump()

    write_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "tool": "check_tubing",
        "arguments": arguments,
        "response": result,
    })

    return result


if __name__ == "__main__":
    mcp.run()
