from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from research_finder.cli.components.empty_state import empty_state
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_confirm
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import truncate
from research_finder.database.connection import get_session_factory
from research_finder.database.models import Business as BusinessModel
from research_finder.database.website_repository import WebsiteAnalysisRepository
from research_finder.providers.website import WebsiteAnalyzer


class WebsiteAuditScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Analyze business websites for online presence")

        session_factory = get_session_factory()
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(BusinessModel).where(
                    BusinessModel.website.isnot(None),
                    BusinessModel.website != ""
                ).order_by(BusinessModel.total_score.desc().nullslast())
            )
            businesses = list(result.scalars().all())

        if not businesses:
            empty_state(
                self.console,
                "No businesses with websites found.",
                hint="Discover businesses first."
            )
            print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
            return

        table = Table(
            title=f"Businesses with Websites ({len(businesses[:20])})",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold", max_width=30)
        table.add_column("Website", max_width=35)
        table.add_column("Score", justify="center")

        for i, biz in enumerate(businesses[:20], 1):
            score_str = f"{biz.total_score:.0f}" if biz.total_score else "-"
            table.add_row(
                str(i),
                truncate(biz.name, 28),
                truncate(biz.website, 33),
                score_str
            )

        self.console.print(table)
        self.console.print()

        if not await ask_confirm("Analyze all displayed websites?", default=False):
            print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
            return

        analyzer = WebsiteAnalyzer()
        analyzed = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Analyzing 0/{len(businesses[:20])}...", total=len(businesses[:20])
            )

            for biz in businesses[:20]:
                if not biz.website:
                    continue

                progress.update(task, description=f"Analyzing {biz.name[:30]}...")
                result = await analyzer.analyze(biz.website)

                async with session_factory() as session:
                    repo = WebsiteAnalysisRepository(session)
                    await repo.save(biz.id, result.to_dict())

                analyzed += 1
                progress.advance(task)

        print_status(self.console, f"Analyzed {analyzed} websites!", "success")
        self.console.print("  [bold]Use the main menu to view details.[/bold]")
        self.console.print()

        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
