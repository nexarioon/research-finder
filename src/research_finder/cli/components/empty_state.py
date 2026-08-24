from __future__ import annotations

from rich.console import Console


def empty_state(
    console: Console,
    message: str,
    *,
    hint: str | None = None,
    action: str | None = None,
) -> None:
    console.print()
    console.print(f"  [dim]{message}[/dim]")
    if hint:
        console.print(f"  [dim]{hint}[/dim]")
    if action:
        console.print()
        console.print(f"  [bold cyan]\u203a[/bold cyan] {action}")
    console.print()
