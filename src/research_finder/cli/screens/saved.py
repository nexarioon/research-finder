from __future__ import annotations

from rich.console import Console
from rich.table import Table

from research_finder.cli.components.empty_state import empty_state
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_select, ask_text
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import format_number, format_score, truncate
from research_finder.database.connection import get_session_factory
from research_finder.database.models import Business, BusinessStatus


class SavedScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "View and manage your saved research candidates")

        session_factory = get_session_factory()
        async with session_factory() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Business).where(Business.status.in_([
                    BusinessStatus.SAVED,
                    BusinessStatus.QUALIFIED,
                    BusinessStatus.ANALYZED,
                ])).order_by(Business.total_score.desc().nullslast(), Business.name)
            )
            businesses = list(result.scalars().all())

        if not businesses:
            empty_state(
                self.console,
                "No saved businesses yet.",
                hint="Discover businesses first, then save them."
            )
            print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
            return

        self._show_table(businesses)
        await self._handle_actions(businesses)

        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    def _show_table(self, businesses: list[Business]) -> None:
        table = Table(
            title=f"Saved Businesses ({len(businesses)})",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold", max_width=28)
        table.add_column("Category", max_width=16)
        table.add_column("Rating", justify="center", width=6)
        table.add_column("Reviews", justify="center", width=7)
        table.add_column("Score", justify="center", width=5)
        table.add_column("Status", justify="center", width=10)

        for i, biz in enumerate(businesses, 1):
            status_style = {
                BusinessStatus.SAVED: "yellow",
                BusinessStatus.QUALIFIED: "cyan",
                BusinessStatus.ANALYZED: "green",
            }.get(biz.status, "white")
            table.add_row(
                str(i),
                truncate(biz.name, 26),
                truncate(biz.category, 14),
                f"{biz.rating:.1f}" if biz.rating else "-",
                format_number(biz.review_count),
                format_score(biz.total_score),
                f"[{status_style}]{biz.status.value}[/{status_style}]"
            )

        self.console.print(table)
        self.console.print()

    async def _handle_actions(self, businesses: list[Business]) -> None:
        choice = await ask_select(
            "What would you like to do?",
            [
                "View business details",
                "Back to menu",
            ],
            
        )

        if choice == "View business details":
            await self._view_detail(businesses)

    async def _view_detail(self, businesses: list[Business]) -> None:
        nums = await ask_text("Enter business number to view:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(businesses):
                biz = businesses[idx]
                from rich.panel import Panel
                self.console.print()
                self.console.print(Panel(
                    f"[bold]{biz.name}[/bold]\n\n"
                    f"Category:  {biz.category or '-'}\n"
                    f"Address:   {biz.address or '-'}\n"
                    f"Phone:     {biz.phone or '-'}\n"
                    f"Email:     {biz.email or '-'}\n"
                    f"Website:   {biz.website or '-'}\n"
                    f"Rating:    {biz.rating or '-'}\n"
                    f"Reviews:   {biz.review_count or '-'}\n"
                    f"Score:     {format_score(biz.total_score)}\n"
                    f"Status:    {biz.status.value}\n"
                    f"Source:    {biz.source or '-'}",
                    title="Business Details",
                    border_style="cyan"
                ))
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")
