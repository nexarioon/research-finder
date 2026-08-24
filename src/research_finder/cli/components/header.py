from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

APP_NAME = "Research Prospect Finder"
APP_VERSION = "0.1.0"


def print_header(console: Console, subtitle: str | None = None) -> None:
    title = f"[bold]{APP_NAME}[/bold]  [dim]v{APP_VERSION}[/dim]"
    console.print(
        Panel.fit(
            title,
            subtitle=subtitle or "Discover local businesses for research",
            border_style="cyan",
            padding=(0, 1),
        )
    )
    console.print()
