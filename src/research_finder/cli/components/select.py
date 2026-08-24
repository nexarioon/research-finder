from __future__ import annotations

import questionary
from rich.console import Console


def select(
    console: Console,
    message: str,
    choices: list[str],
    *,
    default: str | None = None,
) -> str | None:
    if not choices:
        return None

    styled_choices = [
        questionary.Choice(title=c, value=c) for c in choices
    ]

    answer = questionary.select(
        message,
        choices=styled_choices,
        default=default,
        qmark="\u203a",
        pointer="\u203a",
        style=questionary.Style([
            ("question", "bold cyan"),
            ("selected", "bold cyan"),
            ("pointer", "bold cyan"),
            ("highlighted", "bold cyan"),
            ("answer", "bold cyan"),
        ]),
    ).ask()

    return answer


def select_index(
    console: Console,
    message: str,
    choices: list[str],
    *,
    default: int | None = None,
) -> int | None:
    default_val = choices[default] if default is not None else None
    result = select(console, message, choices, default=default_val)
    if result is None:
        return None
    try:
        return choices.index(result)
    except ValueError:
        return None
