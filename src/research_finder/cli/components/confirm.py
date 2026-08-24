from __future__ import annotations

import questionary
from rich.console import Console


def confirm(
    console: Console,
    message: str,
    *,
    default: bool = False,
) -> bool:
    answer = questionary.confirm(
        message,
        default=default,
        qmark="\u203a",
        style=questionary.Style([
            ("question", "bold cyan"),
            ("selected", "bold cyan"),
            ("pointer", "bold cyan"),
            ("highlighted", "bold cyan"),
            ("answer", "bold cyan"),
        ]),
    ).ask()

    return answer if answer is not None else False
