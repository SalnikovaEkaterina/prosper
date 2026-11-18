
from pydantic import BaseModel, Field


class TubingInput(BaseModel):
    """Исходные данные одной секции НКТ."""

    well_id: str = Field(min_length=1)
    od_mm: float = Field(gt=0)
    wall_mm: float = Field(gt=0)
    id_mm: float = Field(gt=0)


class AgentResult(BaseModel):
    """Единый формат ответа агента."""

    status: str
    well_id: str
    trace_id: str
    result: dict | None = None
    reason: str = ""
