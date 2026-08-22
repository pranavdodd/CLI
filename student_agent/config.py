from __future__ import annotations

from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    openai_api_key: Optional[str] = None
    canvas_base_url: Optional[str] = None
    canvas_access_token: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    database_url: str = "sqlite:///student_agent.db"
    default_timezone: str = "America/Chicago"
    max_agent_iterations: int = Field(default=8, ge=1, le=50)
    tool_timeout_seconds: float = Field(default=30.0, gt=0)
    max_tool_output_chars: int = Field(default=50000, ge=1000)

    @property
    def canvas_configured(self) -> bool:
        return bool(self.canvas_base_url and self.canvas_access_token)

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key)

    def validate_canvas(self) -> None:
        if not self.canvas_configured:
            raise ValueError("Canvas integration is not configured. Set CANVAS_BASE_URL and CANVAS_ACCESS_TOKEN.")


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        openai_api_key=_env("OPENAI_API_KEY"),
        canvas_base_url=_env("CANVAS_BASE_URL"),
        canvas_access_token=_env("CANVAS_ACCESS_TOKEN"),
        google_client_id=_env("GOOGLE_CLIENT_ID"),
        google_client_secret=_env("GOOGLE_CLIENT_SECRET"),
        database_url=_env("DATABASE_URL") or "sqlite:///student_agent.db",
        default_timezone=_env("DEFAULT_TIMEZONE") or "America/Chicago",
        max_agent_iterations=int(_env("MAX_AGENT_ITERATIONS") or 8),
        tool_timeout_seconds=float(_env("TOOL_TIMEOUT_SECONDS") or 30),
        max_tool_output_chars=int(_env("MAX_TOOL_OUTPUT_CHARS") or 50000),
    )


def _env(name: str) -> Optional[str]:
    import os

    value = os.getenv(name)
    return value.strip() if value else None
