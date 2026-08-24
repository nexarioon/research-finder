from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console

from research_finder.cli.components.header import APP_NAME, APP_VERSION
from research_finder.cli.components.prompts import ask_select


class Screen(Enum):
    DASHBOARD = "dashboard"
    DISCOVER = "discover"
    SAVED = "saved"
    ANALYZE = "analyze"
    OPPORTUNITIES = "opportunities"
    TOPICS = "topics"
    OUTREACH = "outreach"
    EXPORT = "export"
    SETTINGS = "settings"


SCREEN_LABELS = {
    Screen.DASHBOARD: "Dashboard",
    Screen.DISCOVER: "Discover Businesses",
    Screen.SAVED: "Saved Businesses",
    Screen.ANALYZE: "Analyze Prospects",
    Screen.OPPORTUNITIES: "Research Opportunities",
    Screen.TOPICS: "Research Topics",
    Screen.OUTREACH: "Outreach",
    Screen.EXPORT: "Export Data",
    Screen.SETTINGS: "Settings",
}


MAIN_MENU_ORDER = [
    Screen.DASHBOARD,
    Screen.DISCOVER,
    Screen.SAVED,
    Screen.ANALYZE,
    Screen.OPPORTUNITIES,
    Screen.TOPICS,
    Screen.OUTREACH,
    Screen.EXPORT,
    Screen.SETTINGS,
]


@dataclass
class ShellState:
    current_screen: Screen = Screen.DASHBOARD
    screen_stack: list[Screen] = field(default_factory=list)
    is_interactive: bool = True
    json_output: bool = False

    def navigate(self, screen: Screen) -> None:
        self.screen_stack.append(self.current_screen)
        self.current_screen = screen

    def go_back(self) -> bool:
        if self.screen_stack:
            self.current_screen = self.screen_stack.pop()
            return True
        return False


class Shell:
    def __init__(self, console: Console) -> None:
        self.console = console
        self.state = ShellState()
        self._screens: dict[Screen, object] = {}
        self._running = True

    async def run(self) -> None:
        from research_finder.cli.components.welcome import show_welcome
        from research_finder.database.connection import init_db

        try:
            self.console.print(f"  [dim]Initializing {APP_NAME}...[/dim]")
            await init_db()
        except Exception as e:
            self.console.print(f"  [red]\u2717 Failed to initialize: {e}[/red]")
            return

        await show_welcome(self.console)

        while self._running:
            self.console.clear()
            self._print_dashboard_header()

            try:
                choice = await self._show_main_menu()
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n  [green]\u2713 Goodbye![/green]\n")
                break

            if choice is None:
                self.console.print("\n  [green]\u2713 Goodbye![/green]\n")
                break

            if choice == "exit":
                self.console.print("\n  [green]\u2713 Goodbye![/green]\n")
                break

            screen = self._resolve_screen(choice)
            if screen is None:
                continue

            self.state.navigate(screen)

            try:
                await self._run_screen(screen)
            except KeyboardInterrupt:
                self.console.print("\n  [yellow]Interrupted[/yellow]")
            except Exception as e:
                from research_finder.cli.components.error_state import error_state
                error_state(
                    self.console,
                    f"Screen error: {type(e).__name__}",
                    message=str(e),
                    suggestions=["Run with --debug for technical details."],
                )
                self._wait_for_enter()

    def _print_dashboard_header(self) -> None:
        self.console.print()
        self.console.print(
            f"  [bold]{APP_NAME}[/bold]  [dim]v{APP_VERSION}[/dim]"
        )
        self.console.print("  [dim]Your research pipeline[/dim]")
        self.console.print()

    async def _show_main_menu(self) -> str | None:
        labels = []
        for screen in MAIN_MENU_ORDER:
            labels.append(SCREEN_LABELS[screen])
        labels.append("Exit")

        choices = await ask_select(
            "What would you like to do?",
            labels + ["Exit"],
        )

        if choices is None:
            return "exit"

        if choices == "Exit":
            return "exit"

        try:
            idx = labels.index(choices)
            return MAIN_MENU_ORDER[idx].value
        except (ValueError, IndexError):
            return None

    def _resolve_screen(self, key: str) -> Screen | None:
        try:
            return Screen(key)
        except ValueError:
            return None

    async def _run_screen(self, screen: Screen) -> None:
        screen_obj = self._get_screen_instance(screen)
        if screen_obj and hasattr(screen_obj, "run"):
            await screen_obj.run()
        self.state.go_back()

    def _get_screen_instance(self, screen: Screen) -> object | None:
        if screen not in self._screens:
            self._screens[screen] = self._create_screen(screen)
        return self._screens.get(screen)

    def _create_screen(self, screen: Screen) -> object | None:
        if screen == Screen.DASHBOARD:
            from research_finder.cli.screens.dashboard import DashboardScreen
            return DashboardScreen(self.console)
        elif screen == Screen.DISCOVER:
            from research_finder.cli.screens.discover import DiscoverScreen
            return DiscoverScreen(self.console)
        elif screen == Screen.SAVED:
            from research_finder.cli.screens.saved import SavedScreen
            return SavedScreen(self.console)
        elif screen == Screen.ANALYZE:
            from research_finder.cli.screens.analyze import AnalyzeScreen
            return AnalyzeScreen(self.console)
        elif screen == Screen.OPPORTUNITIES:
            from research_finder.cli.screens.opportunities import OpportunitiesScreen
            return OpportunitiesScreen(self.console)
        elif screen == Screen.TOPICS:
            from research_finder.cli.screens.topics import TopicsScreen
            return TopicsScreen(self.console)
        elif screen == Screen.OUTREACH:
            from research_finder.cli.screens.outreach import OutreachScreen
            return OutreachScreen(self.console)
        elif screen == Screen.EXPORT:
            from research_finder.cli.screens.export import ExportScreen
            return ExportScreen(self.console)
        elif screen == Screen.SETTINGS:
            from research_finder.cli.screens.settings import SettingsScreen
            return SettingsScreen(self.console)
        return None

    def _wait_for_enter(self) -> None:
        try:
            input("\n  Press Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            pass
