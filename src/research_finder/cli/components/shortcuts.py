from __future__ import annotations

from rich.console import Console


def print_shortcuts(
    console: Console,
    shortcuts: list[tuple[str, str]] | None = None,
) -> None:
    if shortcuts is None:
        shortcuts = [
            ("\u2191\u2193", "Navigate"),
            ("Enter", "Select"),
            ("/", "Search"),
            ("Esc", "Back"),
            ("q", "Quit"),
            ("?", "Help"),
        ]

    parts = []
    for key, label in shortcuts:
        parts.append(f"[dim]{key}[/dim] {label}")

    console.print()
    console.print("  " + "   ".join(parts))
    console.print()
