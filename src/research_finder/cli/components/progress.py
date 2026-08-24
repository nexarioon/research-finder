from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.status import Status


def run_progress(
    console: Console,
    description: str,
    total: int | None = None,
    *,
    show_bar: bool = False,
) -> Progress:
    columns = [SpinnerColumn(), TextColumn("[progress.description]{task.description}")]
    if show_bar and total:
        columns.extend([
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ])
    return Progress(*columns, console=console)


async def run_with_spinner(
    console: Console,
    description: str,
    coro: Awaitable,
):
    with Status(description, console=console, spinner="dots"):
        return await coro


def run_steps(
    console: Console,
    steps: list[tuple[str, Callable[[], Awaitable]]],
) -> None:
    asyncio.run(_run_steps_async(console, steps))


async def _run_steps_async(
    console: Console,
    steps: list[tuple[str, Callable[[], Awaitable]]],
) -> None:
    for i, (name, step_fn) in enumerate(steps):
        prefix = "\u2713" if i < len(steps) - 1 else "\u2192"
        style = "green" if i < len(steps) - 1 else "cyan"
        console.print(f"  [{style}]{prefix}[/{style}] {name}")
        await step_fn()
    console.print()
