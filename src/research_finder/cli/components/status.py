from __future__ import annotations

from rich.console import Console

SYMBOLS = {
    "success": "\u2713",
    "warning": "\u26a0",
    "error": "\u2717",
    "info": "\u2139",
    "running": "\u25b6",
}

STYLES = {
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "cyan",
    "running": "cyan",
}


def print_status(
    console: Console,
    message: str,
    status: str = "info",
    *,
    indent: int = 2,
) -> None:
    symbol = SYMBOLS.get(status, "\u2022")
    style = STYLES.get(status, "white")
    padding = " " * indent
    console.print(f"{padding}[{style}]{symbol}[/{style}] {message}")
