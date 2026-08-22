import pytest
from pydantic import BaseModel

from student_agent.agent.conversation import Conversation
from student_agent.agent.engine import AgentEngine, LLMResponse
from student_agent.tools.base import make_tool
from student_agent.tools.registry import ToolRegistry


class Args(BaseModel):
    value: int


class FakeLLM:
    def __init__(self):
        self.calls = 0

    async def generate(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(tool_calls=[{"id": "1", "name": "double", "arguments": {"value": 3}}])
        return LLMResponse(text="The result is 6.")


@pytest.mark.asyncio
async def test_agent_chains_tool_and_final_response():
    async def double(value: int):
        return value * 2

    registry = ToolRegistry()
    registry.register(make_tool("double", "Double a value.", Args, double))
    engine = AgentEngine(FakeLLM(), registry, Conversation("test"), max_iterations=2)
    assert await engine.run("calculate") == "The result is 6."
