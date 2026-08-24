"""Screen components for the TUI."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, DataTable, Label

from research_finder.database.connection import get_session
from research_finder.database.opportunity_repository import OpportunityRepository
from research_finder.database.outreach_repository import OutreachRepository
from research_finder.database.repositories import BusinessRepository


class DashboardScreen(Container):
    """Dashboard screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Dashboard[/bold cyan]", classes="screen-title")
        yield Label("[dim]Overview of your research pipeline[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Export Data", variant="primary", id="btn-export"),
            Button("Backup DB", variant="default", id="btn-backup"),
            Button("AI Budget", variant="default", id="btn-ai"),
            classes="button-row"
        )

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Metric", "Count")
        
        try:
            async with get_session() as session:
                business_repo = BusinessRepository(session)
                all_businesses = await business_repo.get_all()
                saved_businesses = await business_repo.get_saved()
                qualified_businesses = await business_repo.get_qualified()
                
                table.add_row("Discovered", str(len(all_businesses)))
                table.add_row("Qualified", str(len(qualified_businesses)))
                table.add_row("Saved", str(len(saved_businesses)))
                table.add_row("Analyzed", "0")
                table.add_row("Opportunities", "0")
                table.add_row("Topics", "0")
                table.add_row("Outreach", "0")
        except Exception:
            table.add_row("Discovered", "0")
            table.add_row("Qualified", "0")
            table.add_row("Saved", "0")
            table.add_row("Analyzed", "0")
            table.add_row("Opportunities", "0")
            table.add_row("Topics", "0")
            table.add_row("Outreach", "0")


class DiscoverScreen(Container):
    """Business discovery screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Discover Businesses[/bold cyan]", classes="screen-title")
        yield Label("[dim]Search for local businesses using OpenStreetMap[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Auto-detect Location", variant="primary", id="btn-auto"),
            Button("Enter Address", variant="default", id="btn-address"),
            Button("Enter Coordinates", variant="default", id="btn-coords"),
            classes="button-row"
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Name", "Category", "Address", "Score")
        table.add_row("Click a button to start discovery", "", "", "")


class SavedScreen(Container):
    """Saved businesses screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Saved Businesses[/bold cyan]", classes="screen-title")
        yield Label("[dim]View and manage your saved research candidates[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Name", "Category", "Rating", "Score", "Status")
        
        try:
            async with get_session() as session:
                business_repo = BusinessRepository(session)
                saved_businesses = await business_repo.get_saved()
                
                if saved_businesses:
                    for business in saved_businesses:
                        table.add_row(
                            business.name or "Unknown",
                            business.category or "Unknown",
                            str(business.rating or ""),
                            str(business.scoring_total or ""),
                            business.status or "discovered"
                        )
                else:
                    table.add_row("No saved businesses yet", "", "", "", "")
        except Exception:
            table.add_row("No saved businesses yet", "", "", "", "")


class AnalyzeScreen(Container):
    """Analyze prospects screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Analyze Prospects[/bold cyan]", classes="screen-title")
        yield Label("[dim]Score and rank business candidates[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Score All", variant="primary", id="btn-score"),
            Button("Filter by Score", variant="default", id="btn-filter"),
            Button("Select Top Candidates", variant="default", id="btn-select"),
            classes="button-row"
        )

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("#", "Name", "Score", "Size", "Online", "Contact")
        
        try:
            async with get_session() as session:
                business_repo = BusinessRepository(session)
                qualified_businesses = await business_repo.get_qualified()
                
                if qualified_businesses:
                    for i, business in enumerate(qualified_businesses[:20], 1):  # Show top 20
                        table.add_row(
                            str(i),
                            business.name or "Unknown",
                            str(business.scoring_total or ""),
                            business.estimated_size or "unknown",
                            "yes" if business.has_website else "no",
                            "yes" if business.has_email else "no"
                        )
                else:
                    table.add_row("No qualified businesses yet", "", "", "", "", "")
        except Exception:
            table.add_row("Run scoring first", "", "", "", "", "")


class OpportunitiesScreen(Container):
    """Research opportunities screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Research Opportunities[/bold cyan]", classes="screen-title")
        yield Label("[dim]Discover potential research topics from analyzed businesses[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Auto-detect Topics", variant="primary", id="btn-detect"),
            Button("View All", variant="default", id="btn-view-all"),
            Button("Filter by Score", variant="default", id="btn-filter"),
            classes="button-row"
        )

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Business", "Domain", "Opportunity", "Score")
        
        try:
            async with get_session() as session:
                opportunity_repo = OpportunityRepository(session)
                opportunities = await opportunity_repo.get_all()
                
                if opportunities:
                    for opp in opportunities[:20]:  # Show top 20
                        table.add_row(
                            str(opp.business_id),
                            opp.category or "Unknown",
                            opp.title or "Unknown",
                            ""
                        )
                else:
                    table.add_row("No opportunities yet", "", "", "")
        except Exception:
            table.add_row("No opportunities yet", "", "", "")


class TopicsScreen(Container):
    """Research topics screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Research Topics[/bold cyan]", classes="screen-title")
        yield Label("[dim]Organize and manage your research topics[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Create Topic", variant="primary", id="btn-create"),
            Button("View Notes", variant="default", id="btn-notes"),
            Button("Export", variant="default", id="btn-export"),
            classes="button-row"
        )

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Topic", "Businesses", "Priority", "Status")
        
        try:
            async with get_session() as session:
                from research_finder.database.opportunity_repository import TopicRepository
                topic_repo = TopicRepository(session)
                topics = await topic_repo.get_saved()
                
                if topics:
                    for topic in topics:
                        table.add_row(
                            topic.title or "Untitled",
                            str(topic.business_id),
                            "",
                            "saved" if topic.is_saved else "unsaved"
                        )
                else:
                    table.add_row("No topics yet", "", "", "")
        except Exception:
            table.add_row("No topics yet", "", "", "")


class OutreachScreen(Container):
    """Outreach screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Outreach[/bold cyan]", classes="screen-title")
        yield Label("[dim]Manage email drafts and track outreach status[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Create Draft", variant="primary", id="btn-create"),
            Button("Preview", variant="default", id="btn-preview"),
            Button("Send", variant="success", id="btn-send"),
            classes="button-row"
        )

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Business", "Template", "Status", "Created")
        
        try:
            async with get_session() as session:
                outreach_repo = OutreachRepository(session)
                outreach_messages = await outreach_repo.get_all()
                
                if outreach_messages:
                    for msg in outreach_messages[:20]:  # Show recent 20
                        table.add_row(
                            str(msg.business_id),
                            msg.email_subject[:30] + "..." if len(msg.email_subject) > 30 else msg.email_subject,
                            msg.status.value if msg.status else "draft",
                            msg.created_at.strftime("%Y-%m-%d") if msg.created_at else ""
                        )
                else:
                    table.add_row("No outreach yet", "", "", "")
        except Exception:
            table.add_row("No outreach yet", "", "", "")


class SettingsScreen(Container):
    """Settings screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Settings[/bold cyan]", classes="screen-title")
        yield Label("[dim]Configure API keys, preferences, and defaults[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Save Settings", variant="primary", id="btn-save"),
            Button("Reset Defaults", variant="default", id="btn-reset"),
            classes="button-row"
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Setting", "Value", "Status")
        table.add_row("RF_OPENAI_API_KEY", "***", "configured")
        table.add_row("RF_OPENAI_BASE_URL", "https://api.openai.com/v1", "default")
        table.add_row("RF_OPENAI_MODEL", "gpt-4o-mini", "default")
        table.add_row("RF_DEFAULT_RADIUS_KM", "5", "default")
        table.add_row("RF_DATA_DIR", "./data", "default")


class ExportScreen(Container):
    """Export screen."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Export Data[/bold cyan]", classes="screen-title")
        yield Label("[dim]Export your research data in various formats[/dim]", classes="screen-subtitle")
        yield DataTable(classes="content-table")
        yield Horizontal(
            Button("Export CSV", variant="primary", id="btn-csv"),
            Button("Export JSON", variant="default", id="btn-json"),
            Button("Export Markdown", variant="default", id="btn-md"),
            Button("Backup Database", variant="success", id="btn-backup"),
            classes="button-row"
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Format", "File", "Status")
        table.add_row("No exports yet", "", "")
