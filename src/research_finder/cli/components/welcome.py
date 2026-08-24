"""Welcome screen shown on first launch."""
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text

from research_finder.cli.components.header import APP_NAME, APP_VERSION
from research_finder.cli.components.prompts import ask_text

WELCOME_FILE = Path("data/.welcome_seen")


def _has_seen_welcome() -> bool:
    return WELCOME_FILE.exists()


def _mark_welcome_seen() -> None:
    WELCOME_FILE.parent.mkdir(parents=True, exist_ok=True)
    WELCOME_FILE.write_text("1", encoding="utf-8")


async def show_welcome(console: Console) -> None:
    if _has_seen_welcome():
        return

    console.clear()
    console.print()

    # ASCII art logo
    logo = Text()
    logo.append("  _____ _           _                    _____ _           _   \n")
    logo.append(" |  ___(_)_ __   __| | ___  _ __ ___   |  ___(_)_ __   __| | \n")
    logo.append(" | |_  | | '_ \\ / _` |/ _ \\| '_ ` _ \\  | |_  | | '_ \\ / _` | \n")
    logo.append(" |  _| | | | | | (_| | (_) | | | | | | |  _| | | | | | (_| | \n")
    logo.append(" |_|   |_|_| |_|\\__,_|\\___/|_| |_| |_| |_|   |_|_| |_|\\__,_| \n")
    logo.append("\n")
    logo.append(f"  v{APP_VERSION}", style="dim")
    console.print(logo)

    console.print("  A modern CLI for thesis research.", style="dim")
    console.print()

    # Features
    features = (
        "[bold cyan]\u25b6[/bold cyan] [bold]Discover[/bold]  "
        "Find local businesses via OpenStreetMap\n"
        "[bold cyan]\u25b6[/bold cyan] [bold]Analyze[/bold]   "
        "Score & rank by research potential\n"
        "[bold cyan]\u25b6[/bold cyan] [bold]Research[/bold]  "
        "AI-powered insights & topic generation\n"
        "[bold cyan]\u25b6[/bold cyan] [bold]Outreach[/bold]  "
        "Email drafts & contact management"
    )
    console.print(features)
    console.print()

    # Quick commands
    console.print("  [bold]Quick Commands[/bold]")
    console.print()
    console.print("    [cyan]research-finder[/cyan]              Launch interactive mode")
    console.print("    [cyan]research-finder scan[/cyan]          Discover businesses")
    console.print("    [cyan]research-finder results[/cyan]       Browse saved data")
    console.print("    [cyan]research-finder --help[/cyan]        Show all commands")
    console.print()

    # Keyboard shortcuts
    console.print("  [dim]Keys: \u2191\u2193 Navigate  Enter Select  / Search  Esc Back  q Quit[/dim]")
    console.print()

    # Wait for user
    await ask_text("Press Enter to start...")
    _mark_welcome_seen()
