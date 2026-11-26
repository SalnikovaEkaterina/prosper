from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    CHECK_TUBING = "CHECK_TUBING"
    CREATE_MODEL_PLAN = "CREATE_MODEL_PLAN"
    UPDATE_MODEL_PLAN = "UPDATE_MODEL_PLAN"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class AgentTask(BaseModel):
    """Типизированная задача, полученная из естественно-языкового запроса."""

    task_type: TaskType
    well_id: str | None = None
    od_mm: float | None = Field(default=None, gt=0)
    wall_mm: float | None = Field(default=None, gt=0)
    id_mm: float | None = Field(default=None, gt=0)
    change: dict[str, Any] | None = None
    missing_fields: list[str] = Field(default_factory=list)
    clarification: str = ""


class AgentResult(BaseModel):
    """Единый формат результата агента."""

    status: str
    well_id: str | None = None
    trace_id: str
    result: dict[str, Any] | None = None
    reason: str = ""
    task_type: str = ""
    llm_used: bool = False


class LLMParseRecord(BaseModel):
    """Фрагмент журнала разбора запроса языковой моделью."""

    trace_id: str
    request: str
    parsed_task: dict[str, Any]
    model: str
    mode: str
