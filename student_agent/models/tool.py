from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, ConfigDict, Field


class ToolPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


class ToolDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    permission: ToolPermission = ToolPermission.READ
    argument_model: type[BaseModel] = Field(exclude=True)
    handler: Callable[..., Awaitable[Any]] = Field(exclude=True)

    def schema(self) -> dict[str, Any]:
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": self.argument_model.model_json_schema()}}
