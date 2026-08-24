from __future__ import annotations

from rich.console import Console
from rich.table import Table

from research_finder.cli.components.header import print_header
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.config.settings import get_settings


class SettingsScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "View and manage configuration")

        settings = get_settings()

        table = Table(
            title="Current Configuration",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("Setting", style="bold", min_width=22)
        table.add_column("Value")

        table.add_row("Database URL", settings.database_url)
        table.add_row("AI Enabled", str(settings.ai_enabled))
        table.add_row("AI Model", settings.ai_model)
        table.add_row("AI Max per Run", str(settings.ai_max_analyses_per_run))
        table.add_row("AI Max per Day", str(settings.ai_max_analyses_per_day))
        table.add_row("Default Radius", f"{settings.default_radius_km} km")
        table.add_row("Default Min Rating", str(settings.default_min_rating))
        table.add_row("Default Min Reviews", str(settings.default_min_reviews))
        table.add_row("Log Level", settings.log_level)

        self.console.print(table)
        self.console.print()
        msg = "Edit .env file to change settings. Restart the app to apply."
        self.console.print(f"  [dim]{msg}[/dim]")
        self.console.print()

        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
