from typing import Any

from rich.console import Console

from student_agent.models.tool import ToolDefinition


async def confirm_tool(tool: ToolDefinition, arguments: dict[str, Any]) -> bool:
    console = Console()
    console.print(f"\n[bold yellow]Confirmation required:[/bold yellow] {tool.name}")
    console.print(arguments)
    return console.input("Proceed? [y/N] ").strip().lower() in {"y", "yes"}
