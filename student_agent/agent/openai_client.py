from __future__ import annotations

import httpx

from student_agent.agent.engine import LLMResponse


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 60.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def generate(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model, "messages": messages, "tools": tools, "tool_choice": "auto"})
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]
            calls = []
            for call in message.get("tool_calls", []):
                calls.append({"id": call["id"], "name": call["function"]["name"], "arguments": call["function"].get("arguments", "{}")})
            return LLMResponse(text=message.get("content"), tool_calls=calls or None)
