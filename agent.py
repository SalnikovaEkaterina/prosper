"""Публичная точка входа агента: natural language -> LLM -> MCP -> AgentResult."""
from src.agent.loop import run
from src.agent.schemas import AgentResult

__all__ = ["run", "AgentResult"]
