"""Widget components for the TUI."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, ListItem, Static


class SidebarItem(ListItem):
    """A sidebar navigation item."""

    def __init__(self, label: str, icon: str, screen_name: str) -> None:
        super().__init__()
        self.label_text = label
        self.icon = icon
        self.screen_name = screen_name

    def compose(self) -> ComposeResult:
        yield Label(f"{self.icon}  {self.label_text}")


class StatusBar(Static):
    """A status bar at the bottom."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Label("")


class StatsCard(Static):
    """A stats card widget."""

    def __init__(self, title: str, value: str, icon: str, color: str = "cyan") -> None:
        super().__init__()
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.color}]{self.icon}[/{self.color}]")
        yield Label(f"[bold]{self.value}[/bold]")
        yield Label(f"[dim]{self.title}[/dim]")
