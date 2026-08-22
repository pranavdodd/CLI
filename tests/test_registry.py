import pytest
from pydantic import BaseModel

from student_agent.models.tool import ToolPermission
from student_agent.tools.base import make_tool
from student_agent.tools.registry import ConfirmationRequiredError, ToolRegistry


class Args(BaseModel):
    value: int


@pytest.mark.asyncio
async def test_registry_validates_and_executes_tool():
    async def double(value: int):
        return value * 2

    registry = ToolRegistry()
    registry.register(make_tool("double", "Double a value.", Args, double))
    assert await registry.execute("double", {"value": 4}) == 8


@pytest.mark.asyncio
async def test_registry_requires_confirmation_for_writes():
    async def write(value: int):
        return value

    registry = ToolRegistry(confirmer=None)
    registry.register(make_tool("write", "Write a value.", Args, write, ToolPermission.WRITE))
    with pytest.raises(ConfirmationRequiredError):
        await registry.execute("write", {"value": 1})
