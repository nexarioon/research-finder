from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console

from research_finder.cli.components.header import APP_NAME, APP_VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-finder",
        description=f"{APP_NAME} - Discover local businesses for research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  research-finder                    Interactive mode\n"
            "  research-finder scan               Discover businesses\n"
            "  research-finder results            Browse saved businesses\n"
            "  research-finder analyze            Score and rank candidates\n"
            "  research-finder export --format json  Export as JSON\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    scan = sub.add_parser("scan", help="Discover businesses")
    scan.add_argument("--location", type=str, help="Search location")
    scan.add_argument("--radius", type=float, default=5.0, help="Search radius in km")
    scan.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")

    sub.add_parser("results", help="Browse saved businesses").add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )

    sub.add_parser("analyze", help="Score and rank candidates").add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )

    sub.add_parser("opportunities", help="Browse research opportunities").add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )

    sub.add_parser("topics", help="Manage research topics").add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )

    sub.add_parser("outreach", help="Manage outreach")

    exp = sub.add_parser("export", help="Export data")
    exp.add_argument(
        "--format",
        choices=["csv", "json", "markdown"],
        default="json",
        help="Export format (default: json)",
    )

    sub.add_parser("config", help="View configuration")

    sub.add_parser("audit-websites", help="Audit business websites")

    return parser


async def run_interactive() -> None:
    console = Console()
    from research_finder.cli.shell import Shell
    shell = Shell(console)
    await shell.run()


async def run_command(command: str, args: argparse.Namespace) -> None:
    console = Console()

    from research_finder.database.connection import init_db
    await init_db()

    if command == "scan":
        await _run_scan(console, args)
    elif command == "results":
        await _run_results(console, args)
    elif command == "analyze":
        await _run_analyze(console, args)
    elif command == "opportunities":
        await _run_opportunities(console, args)
    elif command == "topics":
        await _run_topics(console, args)
    elif command == "outreach":
        await _run_outreach(console)
    elif command == "export":
        await _run_export(console, args)
    elif command == "config":
        await _run_config(console)
    elif command == "audit-websites":
        await _run_audit(console)


async def _run_scan(console: Console, args: argparse.Namespace) -> None:
    from research_finder.cli.screens.discover import DiscoverScreen
    screen = DiscoverScreen(console)
    await screen.run()


async def _run_results(console: Console, args: argparse.Namespace) -> None:
    from research_finder.cli.screens.saved import SavedScreen
    screen = SavedScreen(console)
    await screen.run()


async def _run_analyze(console: Console, args: argparse.Namespace) -> None:
    from research_finder.cli.screens.analyze import AnalyzeScreen
    screen = AnalyzeScreen(console)
    await screen.run()


async def _run_opportunities(console: Console, args: argparse.Namespace) -> None:
    from research_finder.cli.screens.opportunities import OpportunitiesScreen
    screen = OpportunitiesScreen(console)
    await screen.run()


async def _run_topics(console: Console, args: argparse.Namespace) -> None:
    from research_finder.cli.screens.topics import TopicsScreen
    screen = TopicsScreen(console)
    await screen.run()


async def _run_outreach(console: Console) -> None:
    from research_finder.cli.screens.outreach import OutreachScreen
    screen = OutreachScreen(console)
    await screen.run()


async def _run_export(console: Console, args: argparse.Namespace) -> None:
    from research_finder.cli.screens.export import ExportScreen
    screen = ExportScreen(console)
    await screen.run()


async def _run_config(console: Console) -> None:
    from research_finder.cli.screens.settings import SettingsScreen
    screen = SettingsScreen(console)
    await screen.run()


async def _run_audit(console: Console) -> None:
    from research_finder.cli.screens.website_audit import WebsiteAuditScreen
    screen = WebsiteAuditScreen(console)
    await screen.run()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command:
        try:
            asyncio.run(run_command(args.command, args))
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        try:
            asyncio.run(run_interactive())
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    main()
