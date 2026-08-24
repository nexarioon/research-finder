from __future__ import annotations

from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from research_finder.cli.components.header import print_header
from research_finder.cli.components.panel import print_panel
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.config.settings import get_settings
from research_finder.database.connection import get_session_factory
from research_finder.database.models import (
    AIAnalysis,
    Business,
    BusinessStatus,
    Outreach,
    OutreachStatus,
    ResearchOpportunity,
    ResearchTopic,
    WebsiteAnalysis,
)


class DashboardScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Overview of your research pipeline")

        stats = await self._load_stats()

        self._render_overview(stats)
        self._render_pipeline(stats)
        self._render_outreach(stats)

        settings = get_settings()
        if settings.ai_enabled:
            ai_status = "[green]\u2713 Enabled[/green]"
        else:
            ai_status = "[dim]Disabled[/dim]"
        model = settings.ai_model
        self.console.print(f"  [dim]AI: {ai_status}  |  Model: {model}[/dim]")

        self._render_actions()

        print_shortcuts(self.console, [
            ("1-4", "Quick action"),
            ("Esc", "Back"),
            ("q", "Quit"),
        ])

        await self._handle_input()

    async def _load_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        session_factory = get_session_factory()
        async with session_factory() as session:
            from sqlalchemy import func, select

            result = await session.execute(select(func.count(Business.id)))
            stats["total"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(Business.id)).where(Business.status.in_([
                    BusinessStatus.QUALIFIED, BusinessStatus.SAVED, BusinessStatus.ANALYZED,
                ]))
            )
            stats["qualified"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(Business.id)).where(Business.status == BusinessStatus.SAVED)
            )
            stats["saved"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(Business.id)).where(Business.status == BusinessStatus.ANALYZED)
            )
            stats["analyzed"] = result.scalar() or 0

            result = await session.execute(select(func.count(WebsiteAnalysis.id)))
            stats["websites"] = result.scalar() or 0

            result = await session.execute(select(func.count(AIAnalysis.id)))
            stats["ai_analyses"] = result.scalar() or 0

            result = await session.execute(select(func.count(ResearchOpportunity.id)))
            stats["opportunities"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(ResearchOpportunity.id)).where(ResearchOpportunity.is_favorited)
            )
            stats["favorited"] = result.scalar() or 0

            result = await session.execute(select(func.count(ResearchTopic.id)))
            stats["topics"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(ResearchTopic.id)).where(ResearchTopic.is_saved)
            )
            stats["saved_topics"] = result.scalar() or 0

            result = await session.execute(select(func.count(Outreach.id)))
            stats["outreach"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(Outreach.id)).where(Outreach.status == OutreachStatus.SENT)
            )
            stats["sent"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(Outreach.id)).where(Outreach.status == OutreachStatus.REPLIED)
            )
            stats["replies"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(Outreach.id)).where(Outreach.status == OutreachStatus.INTERESTED)
            )
            stats["interested"] = result.scalar() or 0

        return stats

    def _render_overview(self, stats: dict[str, int]) -> None:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="bold", min_width=18)
        table.add_column("Value", justify="right", style="cyan", min_width=6)

        table.add_row("Discovered", str(stats["total"]))
        table.add_row("Qualified", str(stats["qualified"]))
        table.add_row("Websites", str(stats["websites"]))
        table.add_row("AI Analyses", str(stats["ai_analyses"]))
        table.add_row("Opportunities", str(stats["opportunities"]))
        table.add_row("Topics", str(stats["topics"]))
        table.add_row("Outreach", str(stats["outreach"]))

        print_panel(self.console, "", title="Overview")
        self.console.print(table)
        self.console.print()

    def _render_pipeline(self, stats: dict[str, int]) -> None:
        stages = [
            ("Discover", stats["total"], "\u25b6"),
            ("Save", stats["saved"], "\u25b6"),
            ("Analyze", stats["analyzed"], "\u25b6"),
            ("Opportunities", stats["favorited"], "\u2605"),
            ("Topics", stats["saved_topics"], "\u2605"),
        ]

        max_val = max((s[1] for s in stages), default=1) or 1
        bar_width = 20

        self.console.print("  [bold]Pipeline[/bold]")
        self.console.print()
        for label, count, icon in stages:
            filled = int((count / max_val) * bar_width) if max_val > 0 else 0
            bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
            self.console.print(f"    {icon} {label:<14} [cyan]{bar}[/cyan] {count}")
        self.console.print()

    def _render_outreach(self, stats: dict[str, int]) -> None:
        if stats["outreach"] == 0:
            return

        self.console.print("  [bold]Outreach[/bold]")
        self.console.print()
        items = [
            ("Sent", stats["sent"], "green"),
            ("Replies", stats["replies"], "blue"),
            ("Interested", stats["interested"], "bold green"),
        ]
        for label, count, _style in items:
            print_status(self.console, f"{label}: {count}", "success" if count > 0 else "info")
        self.console.print()

    def _render_actions(self) -> None:
        self.console.print("  [bold]Quick Actions[/bold]")
        self.console.print()
        self.console.print("    [cyan]1[/cyan]  Export all data")
        self.console.print("    [cyan]2[/cyan]  Backup database")
        self.console.print("    [cyan]3[/cyan]  AI Budget")
        self.console.print("    [cyan]4[/cyan]  Back to menu")
        self.console.print()

    async def _handle_input(self) -> None:
        while True:
            try:
                choice = input("  \u203a ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "1":
                from research_finder.cli.screens.export import ExportScreen
                await ExportScreen(self.console).run()
                break
            elif choice == "2":
                self._backup_database()
                break
            elif choice == "3":
                await self._show_ai_budget()
                break
            elif choice == "4" or choice == "":
                break
            else:
                self.console.print("  [dim]Invalid option[/dim]")

    def _backup_database(self) -> None:
        import shutil
        from pathlib import Path

        settings = get_settings()
        db_path = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
        if not db_path.exists():
            self.console.print("  [red]\u2717 Database file not found.[/red]")
            return

        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"research_finder_{timestamp}.db"

        shutil.copy2(db_path, backup_path)
        self.console.print(f"  [green]\u2713 Backed up to {backup_path}[/green]")

    async def _show_ai_budget(self) -> None:
        from research_finder.application.ai_service import AIAnalysisService

        service = AIAnalysisService()
        stats = await service.get_usage_stats()

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="bold", min_width=18)
        table.add_column("Value", min_width=10)

        table.add_row("Enabled", "Yes" if stats["enabled"] else "No")
        table.add_row("Model", stats["model"])
        table.add_row("Analyses Today", str(stats["analyses_today"]))
        table.add_row("Max Per Day", str(stats["max_per_day"]))
        table.add_row("Remaining", str(stats["remaining_today"]))
        table.add_row("Tokens Today", str(stats["tokens_today"]))

        print_panel(self.console, "", title="AI Budget")
        self.console.print(table)
        self.console.print()
