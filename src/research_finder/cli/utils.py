from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console


def output_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def output_error(console: Console, message: str) -> None:
    console.print(f"[red]\u2717 {message}[/red]", file=sys.stderr)


def truncate(text: str | None, max_len: int = 30) -> str:
    if not text:
        return "-"
    if len(text) <= max_len:
        return text
    return text[: max_len - 2] + ".."


def format_score(score: float | None) -> str:
    if score is None:
        return "-"
    return f"{score:.0f}"


def format_number(n: int | None) -> str:
    if n is None:
        return "-"
    return f"{n:,}"
