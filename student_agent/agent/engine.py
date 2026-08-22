from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from student_agent.agent.conversation import Conversation, Message
from student_agent.tools.registry import ToolRegistry


class AgentIterationLimitError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    text: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class LLMClient(Protocol):
    async def generate(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse: ...


class AgentEngine:
    def __init__(self, llm: LLMClient, registry: ToolRegistry, conversation: Conversation, max_iterations: int = 8):
        self.llm = llm
        self.registry = registry
        self.conversation = conversation
        self.max_iterations = max_iterations

    async def run(self, user_message: str) -> str:
        self.conversation.add_user(user_message)
        for _ in range(self.max_iterations):
            response = await self.llm.generate(self.conversation.messages(), self.registry.schemas())
            if not response.tool_calls:
                text = response.text or "I could not produce a response."
                self.conversation.add(Message(role="assistant", content=text))
                return text
            self.conversation.add(Message(role="assistant", content=response.text, tool_calls=response.tool_calls))
            for call in response.tool_calls:
                result = await self._execute_call(call)
                self.conversation.add(Message(role="tool", tool_call_id=call["id"], name=call["name"], content=json.dumps(result, default=str)))
        raise AgentIterationLimitError("Agent reached its tool-execution limit before completing the task.")

    async def _execute_call(self, call: dict[str, Any]) -> dict[str, Any]:
        try:
            arguments = call.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            result = await self.registry.execute(call["name"], arguments)
            return {"success": True, "tool": call["name"], "result": result}
        except Exception as exc:
            return {"success": False, "tool": call.get("name"), "error_type": type(exc).__name__, "message": str(exc)}
