from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from student_agent.agent.conversation import Conversation
from student_agent.agent.engine import AgentEngine, AgentIterationLimitError
from student_agent.agent.openai_client import OpenAIClient
from student_agent.agent.prompts import SYSTEM_PROMPT
from student_agent.config import get_settings
from student_agent.integrations.canvas import CanvasAPIError, CanvasClient
from student_agent.security.permissions import confirm_tool
from student_agent.tools.canvas_tools import canvas_tools
from student_agent.tools.registry import ToolRegistry

app = typer.Typer(help="StudentAgent academic and coding assistant.")
console = Console()


def _canvas() -> CanvasClient:
    settings = get_settings()
    settings.validate_canvas()
    return CanvasClient(settings.canvas_base_url or "", settings.canvas_access_token or "", settings.tool_timeout_seconds)


@app.command()
def config() -> None:
    """Show which integrations are configured without exposing secrets."""
    settings = get_settings()
    table = Table(title="StudentAgent configuration")
    table.add_column("Setting")
    table.add_column("Status")
    table.add_row("Canvas", "configured" if settings.canvas_configured else "not configured")
    table.add_row("OpenAI", "configured" if settings.llm_configured else "not configured")
    table.add_row("Timezone", settings.default_timezone)
    table.add_row("Database", settings.database_url)
    console.print(table)


@app.command()
def courses() -> None:
    """List active Canvas courses."""
    async def run() -> None:
        try:
            items = await _canvas().get_courses()
            for item in items:
                console.print(f"{item.id}: {item.name}" + (f" ({item.course_code})" if item.course_code else ""))
        except (ValueError, CanvasAPIError) as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
    asyncio.run(run())


@app.command()
def assignments(days: int = typer.Option(7, min=1, max=90, help="Only show assignments due within this many days.")) -> None:
    """List upcoming Canvas assignments."""
    async def run() -> None:
        try:
            items = await _canvas().get_upcoming_assignments(days)
            if not items:
                console.print("No assignments found in that window.")
                return
            for item in items:
                due = item.due_at.astimezone().strftime("%a %b %-d, %-I:%M %p") if item.due_at else "No due date"
                console.print(f"{due}  {item.name} [dim](course {item.course_id})[/dim]")
        except (ValueError, CanvasAPIError) as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
    asyncio.run(run())


async def _ask(message: str) -> str:
    settings = get_settings()
    if not settings.llm_configured:
        return "LLM integration is not configured. Set OPENAI_API_KEY in .env to use chat."
    registry = ToolRegistry(settings.tool_timeout_seconds, settings.max_tool_output_chars, confirm_tool)
    for tool in canvas_tools(_canvas()):
        registry.register(tool)
    engine = AgentEngine(OpenAIClient(settings.openai_api_key or ""), registry, Conversation(SYSTEM_PROMPT), settings.max_agent_iterations)
    try:
        return await engine.run(message)
    except AgentIterationLimitError as exc:
        return str(exc)
    except Exception as exc:
        return f"I couldn't complete that request: {exc}"


@app.command()
def ask(message: str = typer.Argument(..., help="Question for StudentAgent.")) -> None:
    """Ask one question and exit."""
    console.print(asyncio.run(_ask(message)))


@app.command()
def chat() -> None:
    """Start an interactive StudentAgent conversation."""
    console.print("[bold]StudentAgent[/bold] (type 'exit' to quit)")
    while True:
        message = typer.prompt("StudentAgent", prompt_suffix=" > ", default="", show_default=False)
        if message.strip().lower() in {"exit", "quit"}:
            break
        if not message.strip():
            continue
        console.print(asyncio.run(_ask(message)))


if __name__ == "__main__":
    app()
