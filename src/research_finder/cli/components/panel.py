from __future__ import annotations

from rich.console import Console
from rich.panel import Panel


def print_panel(
    console: Console,
    content: str,
    *,
    title: str | None = None,
    border_style: str = "cyan",
    width: int | None = None,
) -> None:
    console.print(
        Panel(
            content,
            title=f"[bold]{title}[/bold]" if title else None,
            border_style=border_style,
            width=width,
            padding=(0, 1),
        )
    )
