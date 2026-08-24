"""Helper to run questionary prompts inside an async event loop."""
from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any

import questionary

QMARK_STYLE = questionary.Style([
    ("question", "bold cyan"),
    ("selected", "bold cyan"),
    ("pointer", "bold cyan"),
    ("highlighted", "bold cyan"),
    ("answer", "bold cyan"),
    ("checkbox", "cyan"),
    ("check", "bold green"),
])


def _run_in_thread(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a sync function in a thread executor to avoid event loop conflicts."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


async def ask_select(
    message: str,
    choices: list[str],
    *,
    default: str | None = None,
) -> str | None:
    """Async wrapper for questionary.select."""
    styled = [questionary.Choice(title=c, value=c) for c in choices]

    def _ask() -> str | None:
        return questionary.select(
            message,
            choices=styled,
            default=default,
            qmark="\u203a",
            pointer="\u203a",
            style=QMARK_STYLE,
        ).ask()

    return await _run_in_thread(_ask)


async def ask_checkbox(
    message: str,
    choices: list[str],
    *,
    default: list[str] | None = None,
) -> list[str]:
    """Async wrapper for questionary.checkbox."""
    default = default or []
    styled = [
        questionary.Choice(title=c, value=c, checked=c in default)
        for c in choices
    ]

    def _ask() -> list[str] | None:
        return questionary.checkbox(
            message,
            choices=styled,
            qmark="\u203a",
            pointer="\u203a",
            style=QMARK_STYLE,
        ).ask()

    result = await _run_in_thread(_ask)
    return result or []


async def ask_text(message: str) -> str | None:
    """Async wrapper for questionary.text."""

    def _ask() -> str | None:
        return questionary.text(
            message,
            qmark="\u203a",
            style=QMARK_STYLE,
        ).ask()

    return await _run_in_thread(_ask)


async def ask_confirm(message: str, *, default: bool = False) -> bool:
    """Async wrapper for questionary.confirm."""

    def _ask() -> bool | None:
        return questionary.confirm(
            message,
            default=default,
            qmark="\u203a",
            style=QMARK_STYLE,
        ).ask()

    result = await _run_in_thread(_ask)
    return result if result is not None else False
