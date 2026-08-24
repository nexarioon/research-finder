from __future__ import annotations

import questionary
from rich.console import Console


def multiselect(
    console: Console,
    message: str,
    choices: list[str],
    *,
    default: list[str] | None = None,
) -> list[str]:
    if not choices:
        return []

    styled_choices = [
        questionary.Choice(title=c, value=c, checked=c in (default or []))
        for c in choices
    ]

    answer = questionary.checkbox(
        message,
        choices=styled_choices,
        qmark="\u203a",
        pointer="\u203a",
        style=questionary.Style([
            ("question", "bold cyan"),
            ("selected", "bold cyan"),
            ("pointer", "bold cyan"),
            ("highlighted", "bold cyan"),
            ("checkbox", "cyan"),
            ("check", "bold green"),
        ]),
    ).ask()

    return answer or []
