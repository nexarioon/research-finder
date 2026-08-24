from __future__ import annotations

from rich.console import Console


def error_state(
    console: Console,
    title: str,
    *,
    message: str | None = None,
    causes: list[str] | None = None,
    suggestions: list[str] | None = None,
) -> None:
    console.print()
    console.print(f"  [bold red]\u2717 {title}[/bold red]")
    console.print()
    if message:
        console.print(f"  {message}")
        console.print()
    if causes:
        console.print("  [bold]Possible causes:[/bold]")
        for cause in causes:
            console.print(f"    \u2022 {cause}")
        console.print()
    if suggestions:
        console.print("  [bold]Try:[/bold]")
        for suggestion in suggestions:
            console.print(f"    {suggestion}")
        console.print()
