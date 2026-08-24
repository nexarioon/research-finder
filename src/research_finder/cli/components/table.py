from __future__ import annotations

from rich.console import Console
from rich.table import Table


def print_table(
    console: Console,
    columns: list[str],
    rows: list[list[str]],
    *,
    title: str | None = None,
    caption: str | None = None,
    show_lines: bool = True,
    border_style: str = "dim",
    column_styles: list[str | None] | None = None,
    max_widths: list[int | None] | None = None,
) -> Table:
    table = Table(
        title=f"[bold]{title}[/bold]" if title else None,
        caption=caption,
        show_lines=show_lines,
        border_style=border_style,
        title_style="bold",
    )

    for i, col in enumerate(columns):
        style = column_styles[i] if column_styles and i < len(column_styles) else None
        width = max_widths[i] if max_widths and i < len(max_widths) else None
        table.add_column(col, style=style, width=width, no_wrap=False)

    for row in rows:
        table.add_row(*row)

    console.print(table)
    return table
