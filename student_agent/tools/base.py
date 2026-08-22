from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel

from student_agent.models.tool import ToolDefinition, ToolPermission

ModelT = TypeVar("ModelT", bound=BaseModel)


def make_tool(name: str, description: str, argument_model: type[ModelT], handler: Callable[..., Awaitable[Any]], permission: ToolPermission = ToolPermission.READ) -> ToolDefinition:
    return ToolDefinition(name=name, description=description, argument_model=argument_model, handler=handler, permission=permission)
