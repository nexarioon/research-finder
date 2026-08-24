"""Main TUI application for Research Finder."""
from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, ListView

from research_finder.cli.tui.screens import (
    AnalyzeScreen,
    DashboardScreen,
    DiscoverScreen,
    OpportunitiesScreen,
    OutreachScreen,
    SavedScreen,
    SettingsScreen,
    TopicsScreen,
)
from research_finder.cli.tui.styles import RESEARCH_FINDER_CSS
from research_finder.cli.tui.widgets import SidebarItem, StatusBar
from research_finder.database.ai_repository import AIAnalysisRepository
from research_finder.database.connection import get_session, init_db
from research_finder.database.opportunity_repository import OpportunityRepository
from research_finder.database.outreach_repository import OutreachRepository
from research_finder.database.repositories import BusinessRepository
from research_finder.database.scoring_repository import ScoringRepository
from research_finder.database.website_repository import WebsiteAnalysisRepository


class ResearchFinderApp(App):
    """Research Prospect Finder - Modern TUI"""

    CSS = RESEARCH_FINDER_CSS

    BINDINGS = [
        Binding("1", "goto_discover", "Discover", show=True),
        Binding("2", "goto_saved", "Saved", show=True),
        Binding("3", "goto_analyze", "Analyze", show=True),
        Binding("4", "goto_opportunities", "Opportunities", show=True),
        Binding("5", "goto_topics", "Topics", show=True),
        Binding("6", "goto_outreach", "Outreach", show=True),
        Binding("7", "goto_dashboard", "Dashboard", show=True),
        Binding("8", "goto_settings", "Settings", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "quit", "Quit", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._db_initialized = False
        self._business_repo: BusinessRepository | None = None
        self._scoring_repo: ScoringRepository | None = None
        self._website_repo: WebsiteAnalysisRepository | None = None
        self._ai_repo: AIAnalysisRepository | None = None
        self._opportunity_repo: OpportunityRepository | None = None
        self._outreach_repo: OutreachRepository | None = None

    async def _init_database(self) -> None:
        """Initialize database and repositories."""
        if not self._db_initialized:
            await init_db()
            self._db_initialized = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()

        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("🔬", id="sidebar-icon")
                yield Label("Research Finder", id="sidebar-title")
                yield Label("v1.0.0", id="sidebar-subtitle")
                yield ListView(
                    SidebarItem("Discover", "🔍", "discover"),
                    SidebarItem("Saved", "💾", "saved"),
                    SidebarItem("Analyze", "📊", "analyze"),
                    SidebarItem("Opportunities", "💡", "opportunities"),
                    SidebarItem("Topics", "📝", "topics"),
                    SidebarItem("Outreach", "📧", "outreach"),
                    SidebarItem("Dashboard", "📈", "dashboard"),
                    SidebarItem("Settings", "⚙️", "settings"),
                    id="nav-list"
                )

            with Vertical(id="main-content"):
                yield DashboardScreen(id="dashboard")

        yield StatusBar(id="status-bar")

    async def on_mount(self) -> None:
        self.title = "Research Prospect Finder"
        self.sub_title = "Discover local businesses for research"
        self._update_status("Initializing database...")
        
        await self._init_database()
        
        self._update_status("Ready")

    def _update_status(self, message: str) -> None:
        status_bar = self.query_one("#status-bar")
        status_bar.query_one(Label).update(f"[dim]{message}[/dim]")

    def _show_screen(self, screen_class) -> None:
        main = self.query_one("#main-content")
        main.remove_children()
        main.mount(screen_class())

    async def _load_dashboard_data(self) -> None:
        """Load dashboard statistics from database."""
        if not self._db_initialized:
            return
            
        try:
            async with get_session() as session:
                business_repo = BusinessRepository(session)
                ScoringRepository(session)
                WebsiteAnalysisRepository(session)
                AIAnalysisRepository(session)
                OpportunityRepository(session)
                OutreachRepository(session)
                
                # Get counts
                all_businesses = await business_repo.get_all()
                saved_businesses = await business_repo.get_saved()
                qualified_businesses = await business_repo.get_qualified()
                
                # Update dashboard
                dashboard = self.query_one("#dashboard")
                if dashboard:
                    table = dashboard.query_one("DataTable")
                    if table:
                        table.clear()
                        table.add_row("Discovered", str(len(all_businesses)))
                        table.add_row("Qualified", str(len(qualified_businesses)))
                        table.add_row("Saved", str(len(saved_businesses)))
                        table.add_row("Analyzed", "0")
                        table.add_row("Opportunities", "0")
                        table.add_row("Topics", "0")
                        table.add_row("Outreach", "0")
        except Exception as e:
            self._update_status(f"Error loading data: {e}")

    @on(ListView.Selected)
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, SidebarItem):
            screen_map = {
                "discover": DiscoverScreen,
                "saved": SavedScreen,
                "analyze": AnalyzeScreen,
                "opportunities": OpportunitiesScreen,
                "topics": TopicsScreen,
                "outreach": OutreachScreen,
                "dashboard": DashboardScreen,
                "settings": SettingsScreen,
            }
            screen_class = screen_map.get(item.screen_name)
            if screen_class:
                self._show_screen(screen_class)
                self._update_status(f"Viewing: {item.label_text}")
                
                # Load data for specific screens
                if item.screen_name == "dashboard":
                    self.run_worker(self._load_dashboard_data())

    def action_goto_discover(self) -> None:
        self._show_screen(DiscoverScreen)
        self._update_status("Discover")

    def action_goto_saved(self) -> None:
        self._show_screen(SavedScreen)
        self._update_status("Saved")

    def action_goto_analyze(self) -> None:
        self._show_screen(AnalyzeScreen)
        self._update_status("Analyze")

    def action_goto_opportunities(self) -> None:
        self._show_screen(OpportunitiesScreen)
        self._update_status("Opportunities")

    def action_goto_topics(self) -> None:
        self._show_screen(TopicsScreen)
        self._update_status("Topics")

    def action_goto_outreach(self) -> None:
        self._show_screen(OutreachScreen)
        self._update_status("Outreach")

    def action_goto_settings(self) -> None:
        self._show_screen(SettingsScreen)
        self._update_status("Settings")


def main():
    app = ResearchFinderApp()
    app.run()


if __name__ == "__main__":
    main()
