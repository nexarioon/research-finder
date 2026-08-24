"""CLI screens for each feature."""
from research_finder.cli.screens.analyze import AnalyzeScreen
from research_finder.cli.screens.dashboard import DashboardScreen
from research_finder.cli.screens.discover import DiscoverScreen
from research_finder.cli.screens.opportunities import OpportunitiesScreen
from research_finder.cli.screens.outreach import OutreachScreen
from research_finder.cli.screens.saved import SavedScreen
from research_finder.cli.screens.settings import SettingsScreen
from research_finder.cli.screens.topics import TopicsScreen

__all__ = [
    "DiscoverScreen",
    "SavedScreen",
    "AnalyzeScreen",
    "OpportunitiesScreen",
    "TopicsScreen",
    "OutreachScreen",
    "DashboardScreen",
    "SettingsScreen",
]
