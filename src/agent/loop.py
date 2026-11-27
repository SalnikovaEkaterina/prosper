from __future__ import annotations
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastmcp import Client
from pydantic import ValidationError

from .mcp_server import mcp
from .prompts import SYSTEM_PROMPT, USER_SCHEMA
from .schemas import AgentResult, AgentTask, LLMParseRecord, TaskType

LOG_DIR = Path("logs")
LLM_LOG = LOG_DIR / "llm_calls.jsonl"
AGENT_LOG = LOG_DIR / "agent_runs.jsonl"


def _write_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _offline_parse(request: str) -> AgentTask:
    """Небольшой deterministic fallback для запуска без API-ключа."""
    import re

    low = request.lower()
    if any(x in low for x in ("рассчитай стоимость", "погода", "напиши диплом", "бурение целиком")):
        return AgentTask(task_type=TaskType.OUT_OF_SCOPE, clarification="Запрос не относится к поддерживаемым операциям агента.")

    well = re.search(r"(?:скважин[аы]|well)\s*([A-Za-zА-Яа-я0-9_-]+)", request, re.I)
    nums = [float(x.replace(',', '.')) for x in re.findall(r"\d+(?:[.,]\d+)?", request)]
    if "нкт" in low or "труб" in low or "tubing" in low:
        task = AgentTask(
            task_type=TaskType.CHECK_TUBING,
            well_id=well.group(1) if well else None,
            clarification="",
        )
        # Для типичных фраз: OD 73, стенка 5.5, ID 62.
        for label, pattern in [
            ("od_mm", r"(?:od|наружн(?:ый|ого)\s+диаметр)\s*[=:]?\s*(\d+(?:[.,]\d+)?)"),
            ("wall_mm", r"(?:стенк(?:а|и)|wall)\s*[=:]?\s*(\d+(?:[.,]\d+)?)"),
            ("id_mm", r"(?:id|внутренн(?:ий|его)\s+диаметр)\s*[=:]?\s*(\d+(?:[.,]\d+)?)"),
        ]:
            m = re.search(pattern, low, re.I)
            if m:
                setattr(task, label, float(m.group(1).replace(',', '.')))
        missing = [x for x in ("well_id", "od_mm", "wall_mm", "id_mm") if getattr(task, x) is None]
        task.missing_fields = missing
        return task

    if any(x in low for x in ("новую модель", "создай модель", "new_", "new скваж")):
        return AgentTask(task_type=TaskType.CREATE_MODEL_PLAN, well_id=well.group(1) if well else None)
    if any(x in low for x in ("обнови модель", "ремонт", "rep_", "изменить модель")):
        return AgentTask(task_type=TaskType.UPDATE_MODEL_PLAN, well_id=well.group(1) if well else None)
    return AgentTask(task_type=TaskType.OUT_OF_SCOPE, clarification="Не удалось сопоставить запрос с поддерживаемой операцией.")


def _parse_with_llm(request: str) -> tuple[AgentTask, str, str]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Пакет openai не установлен") from exc

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY не задан")

    model = os.getenv("OPENAI_MODEL", "gpt-6.2-sol")
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=request,
        text={"format": {"type": "json_schema", "name": "agent_task", "strict": True, "schema": USER_SCHEMA}},
    )
    raw = response.output_text
    return AgentTask(**_extract_json(raw)), model, raw


async def _call_mcp(tool_name: str, arguments: dict) -> dict:
    async with Client(mcp) as client:
        response = await client.call_tool(tool_name, arguments)
        return response.data


def run(request: str, ctx: dict | None = None) -> AgentResult:
    """Полный агентный цикл: LLM -> typed task -> validation -> MCP -> AgentResult."""
    trace_id = str(uuid4())
    ctx = ctx or {}
    request = str(request).strip()
    if not request:
        return AgentResult(status="INVALID_REQUEST", trace_id=trace_id, reason="Пустой инженерный запрос.")

    use_llm = ctx.get("use_llm", os.getenv("USE_LLM", "1") != "0")
    model = "offline-fallback"
    mode = "offline"
    try:
        if use_llm:
            task, model, raw_llm = _parse_with_llm(request)
            mode = "openai_responses"
        else:
            task = _offline_parse(request)
            raw_llm = json.dumps(task.model_dump(), ensure_ascii=False)
    except Exception as exc:
        if ctx.get("strict_llm", False):
            return AgentResult(status="LLM_ERROR", trace_id=trace_id, reason=str(exc), llm_used=True)
        task = _offline_parse(request)
        raw_llm = json.dumps(task.model_dump(), ensure_ascii=False)
        mode = "offline_fallback"
        model = "offline-fallback"

    _write_jsonl(LLM_LOG, LLMParseRecord(
        trace_id=trace_id,
        request=request,
        parsed_task=task.model_dump(),
        model=model,
        mode=mode,
    ).model_dump())

    _write_jsonl(AGENT_LOG, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event": "TASK_PARSED",
        "task": task.model_dump(),
        "llm_raw": raw_llm,
    })

    try:
        if task.task_type == TaskType.OUT_OF_SCOPE:
            result = AgentResult(
                status="OUT_OF_SCOPE",
                well_id=task.well_id,
                trace_id=trace_id,
                reason=task.clarification or "Запрос вне области агента.",
                task_type=task.task_type.value,
                llm_used=mode == "openai_responses",
            )
        elif task.task_type == TaskType.CHECK_TUBING:
            if task.missing_fields:
                result = AgentResult(
                    status="MISSING_INPUT",
                    well_id=task.well_id,
                    trace_id=trace_id,
                    reason="Не хватает полей: " + ", ".join(task.missing_fields),
                    task_type=task.task_type.value,
                    llm_used=mode == "openai_responses",
                )
            else:
                mcp_result = __import__("asyncio").run(_call_mcp("check_tubing", {
                    "well_id": task.well_id,
                    "od_mm": task.od_mm,
                    "wall_mm": task.wall_mm,
                    "id_mm": task.id_mm,
                }))
                result = AgentResult(**{**mcp_result, "task_type": task.task_type.value, "llm_used": mode == "openai_responses"})
        elif task.task_type in (TaskType.CREATE_MODEL_PLAN, TaskType.UPDATE_MODEL_PLAN):
            mcp_tool = "prepare_new_model_plan" if task.task_type == TaskType.CREATE_MODEL_PLAN else "prepare_update_model_plan"
            mcp_result = __import__("asyncio").run(_call_mcp(mcp_tool, {"well_id": task.well_id, "change": task.change or {}}))
            result = AgentResult(**{**mcp_result, "task_type": task.task_type.value, "llm_used": mode == "openai_responses"})
        else:
            result = AgentResult(status="NO_SOLUTION", trace_id=trace_id, reason="Неизвестный тип задачи.")
    except Exception as exc:
        result = AgentResult(
            status="TOOL_ERROR",
            well_id=task.well_id,
            trace_id=trace_id,
            reason=f"Ошибка MCP-инструмента: {exc}",
            task_type=task.task_type.value,
            llm_used=mode == "openai_responses",
        )

    _write_jsonl(AGENT_LOG, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event": "AGENT_RESULT",
        "response": result.model_dump(),
    })
    return result
