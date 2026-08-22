from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable

from pydantic import ValidationError

from student_agent.models.tool import ToolDefinition, ToolPermission


class ToolError(RuntimeError):
    pass


class ToolNotFoundError(ToolError):
    pass


class ConfirmationRequiredError(ToolError):
    pass


class ToolRegistry:
    def __init__(self, timeout_seconds: float = 30.0, max_output_chars: int = 50000, confirmer: Callable[[ToolDefinition, dict[str, Any]], Awaitable[bool]] | None = None):
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars
        self.confirmer = confirmer
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"Unknown tool: {name}") from exc

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any], confirm: bool = True) -> Any:
        tool = self.get(name)
        if confirm and tool.permission != ToolPermission.READ:
            if self.confirmer is None or not await self.confirmer(tool, arguments):
                raise ConfirmationRequiredError(f"Confirmation required for {name}.")
        try:
            validated = tool.argument_model.model_validate(arguments)
            result = await asyncio.wait_for(tool.handler(**validated.model_dump()), timeout=self.timeout_seconds)
        except ValidationError as exc:
            raise ToolError(f"Invalid arguments for {name}: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise ToolError(f"Tool {name} timed out.") from exc
        return _truncate(result, self.max_output_chars)


def _truncate(value: Any, maximum: int) -> Any:
    if isinstance(value, str):
        return value if len(value) <= maximum else value[:maximum] + "...[truncated]"
    encoded = json.dumps(value, default=str)
    if len(encoded) <= maximum:
        return value
    return {"success": False, "error_type": "OutputLimitExceeded", "message": f"Tool output exceeded {maximum} characters."}
